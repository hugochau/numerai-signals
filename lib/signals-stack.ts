import * as ec2 from "aws-cdk-lib/aws-ec2";
import * as ecs from "aws-cdk-lib/aws-ecs";
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as glue from 'aws-cdk-lib/aws-glue';
import * as glue_alpha from '@aws-cdk/aws-glue-alpha'
import * as cdk from 'aws-cdk-lib';
import * as events from 'aws-cdk-lib/aws-events';
import * as targets from 'aws-cdk-lib/aws-events-targets';
import * as sns from 'aws-cdk-lib/aws-sns';
import * as s3n from 'aws-cdk-lib/aws-s3-notifications';
import * as sqs from 'aws-cdk-lib/aws-sqs';
import * as subscriptions from 'aws-cdk-lib/aws-sns-subscriptions';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as destinations from 'aws-cdk-lib/aws-logs-destinations';
import { Construct } from 'constructs';


export class SignalsStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // create vpc for our cluster
    const vpc = new ec2.Vpc(this, "SignalsVpc", {
      vpcName: process.env.CDK_DEFAULT_ACCOUNT + '-signals-vpc',
      maxAzs: 2,
      natGateways: 0,
      subnetConfiguration: [
        {
          // 'subnetType' controls Internet access, as described above.
          subnetType: ec2.SubnetType.PUBLIC,
    
          name: 'Public',
          cidrMask: 24,
        },
      ],
    });

    // create cluster for our tasks
    const cluster = new ecs.Cluster(this, "SignalsCluster", {
      clusterName: process.env.CDK_DEFAULT_ACCOUNT + '-signals-cluster',
      vpc: vpc
    });

    // create role for our tasks
    const taskRole = new iam.Role(this, 'SignalsTaskRole', {
      roleName: process.env.CDK_DEFAULT_ACCOUNT + '-signals-task-role',
      assumedBy: new iam.ServicePrincipal('ecs-tasks.amazonaws.com'),
      description: 'IAM role for our tasks',
      // inlinePolicies: {
      //   DescribeACMCerts: describeAcmCertificates,
      // },
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName(
          'AdministratorAccess',
        ),
      ],
    });

    // create task definitions
    // load
    const fargateTaskDefinitionLoad = new ecs.FargateTaskDefinition(this, 'SignalsTaskDefLoad', {
      family:'signals-load',
      memoryLimitMiB: 8192,
      cpu: 1024,
      taskRole: taskRole,
      runtimePlatform: {
        operatingSystemFamily: ecs.OperatingSystemFamily.LINUX,
        cpuArchitecture: ecs.CpuArchitecture.ARM64,
      },
    });

    // transform
    const fargateTaskDefinitionTransform = new ecs.FargateTaskDefinition(this, 'SignalsTaskDefTransform', {
      family:'signals-transform',
      memoryLimitMiB: 8192,
      cpu: 1024,
      taskRole: taskRole,
      runtimePlatform: {
        operatingSystemFamily: ecs.OperatingSystemFamily.LINUX,
        cpuArchitecture: ecs.CpuArchitecture.ARM64,
      },
    });

    // create container image
    const loadLogGroup = new logs.LogGroup(this, 'SignalsLogLoad', {
      logGroupName: `/aws/fargate/${fargateTaskDefinitionLoad.family}`,
      retention: 30
    });

    const transformLogGroup = new logs.LogGroup(this, 'SignalsLogTransform', {
      logGroupName: `/aws/fargate/${fargateTaskDefinitionTransform.family}`,
      retention: 30
    });

    // load
    fargateTaskDefinitionLoad.addContainer("SignalsContainerLoad", {
      containerName: fargateTaskDefinitionLoad.family,
      image: ecs.ContainerImage.fromAsset("./docker/load"),
      logging: ecs.LogDrivers.awsLogs({
        streamPrefix: 'signals',
        logGroup: loadLogGroup})
    });

    // transform
    fargateTaskDefinitionTransform.addContainer("SignalsContainerTransform", {
      containerName: fargateTaskDefinitionTransform.family,
      image: ecs.ContainerImage.fromAsset("./docker/transform"),
      logging: ecs.LogDrivers.awsLogs({
        streamPrefix: 'signals',
        logGroup: transformLogGroup})
    });

    // create cron event
    // target
    const eventRuleTargetLoad = new targets.EcsTask( {
      cluster: cluster,
      taskDefinition: fargateTaskDefinitionLoad,
      subnetSelection: {subnetType: ec2.SubnetType.PUBLIC},
      taskCount: 1
    });

    const eventRuleTargetTransform = new targets.EcsTask( {
      cluster: cluster,
      taskDefinition: fargateTaskDefinitionTransform,
      subnetSelection: {subnetType: ec2.SubnetType.PUBLIC},
      taskCount: 1
    });

    // create schedule for cron event
    new events.Rule(this, 'SignalsRuleLoad', {
      ruleName: process.env.CDK_DEFAULT_ACCOUNT + '-signals-load-cron',
      schedule: events.Schedule.cron({hour: '*/12', minute: '0'}),
      targets: [eventRuleTargetLoad],
    });

    new events.Rule(this, 'SignalsRuleTransform', {
      ruleName: process.env.CDK_DEFAULT_ACCOUNT + '-signals-transform-cron',
      schedule: events.Schedule.cron({weekDay: 'SAT', hour: '1', minute: '0'}),
      targets: [eventRuleTargetTransform],
    });

    const s3Bucket_signals = new s3.Bucket(this, 'SignalsRawDataBucket', {
      bucketName: process.env.CDK_DEFAULT_ACCOUNT + '-signals-data',
      // encryption: s3.BucketEncryption.S3_MANAGED,
    });

    new s3.Bucket(this, 'SignalsAthenaBucket', {
      bucketName: process.env.CDK_DEFAULT_ACCOUNT + '-athena',
    });

    // sns topic
    const s3eventTopic = new sns.Topic(this, 'SignalsS3EventsTopic', {
      topicName: 'signals-s3-events'
    });

    const topicPolicy = new sns.TopicPolicy(this, 'SignalsS3EventsTopicPolicy', {
      topics: [s3eventTopic],
    });
  
    topicPolicy.document.addStatements(new iam.PolicyStatement({
      sid: "s3_to_sns_events_stmt_1",
      effect: iam.Effect.ALLOW,
      principals: [new iam.ServicePrincipal('s3.amazonaws.com')],
      actions: ["sns:Publish"],
      resources: [s3eventTopic.topicArn],
      conditions: {
        "StringEquals": {"aws:SourceAccount": process.env.CDK_DEFAULT_ACCOUNT},
        "ArnLike": {"aws:SourceArn": "arn:aws:s3:*:*:" + s3Bucket_signals.bucketName}
      }
    }));

    s3Bucket_signals.addEventNotification(
      s3.EventType.OBJECT_CREATED,
      new s3n.SnsDestination(s3eventTopic),
      {prefix: 'raw_data'}
    );

    const crawlerS3Policy = new iam.ManagedPolicy(this, 'SignalsCrawlerS3Policy', {
      managedPolicyName: 'signals-glue-crawler-s3-policy',
      document: new iam.PolicyDocument({
        statements: [
          new iam.PolicyStatement({
            effect: iam.Effect.ALLOW,
            actions: [
              "s3:GetObject",
              "s3:PutObject"
            ],
            resources: [
              "arn:aws:s3:::" + s3Bucket_signals.bucketName + "/raw_data/*"
            ],
          })
        ]
      })
    });

    const crawlerSQSPolicy = new iam.ManagedPolicy(this, 'SignalsCrawlerSQSPolicy', {
      managedPolicyName: 'signals-glue-crawler-sqs-policy',
      document: new iam.PolicyDocument({
        statements: [
          new iam.PolicyStatement({
            effect: iam.Effect.ALLOW,
            actions: [
              "sqs:DeleteMessage",
              "sqs:GetQueueUrl",
              "sqs:ListDeadLetterSourceQueues",
              "sqs:ChangeMessageVisibility",
              "sqs:PurgeQueue",
              "sqs:ReceiveMessage",
              "sqs:GetQueueAttributes",
              "sqs:ListQueueTags",
              "sqs:SetQueueAttributes"
            ],
            resources: [
              "arn:aws:sqs:us-east-1:"
                + process.env.CDK_DEFAULT_ACCOUNT
                + ":"
                + s3eventTopic.topicName
            ],
          })
        ]
      })
    });

    const glueRole = new iam.Role(this, 'SignalsGlueRole', {
      roleName: process.env.CDK_DEFAULT_ACCOUNT + '-signals-glue-role',
      assumedBy: new iam.ServicePrincipal('glue.amazonaws.com'),
      description: 'SignalsGlueRole',
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSGlueServiceRole'),
        // iam.ManagedPolicy.fromAwsManagedPolicyName('AmazonS3FullAccess'),
        crawlerS3Policy,
        crawlerSQSPolicy
      ]
    });

    // sql queue
    const sqsQueue = new sqs.Queue(this, 'SignalsQueue', {
      queueName: 'signals-s3-events'
    });

    s3eventTopic.addSubscription(new subscriptions.SqsSubscription(sqsQueue));

    const queuePolicy = new sqs.QueuePolicy(this, 'SignalsQueuePolicy', {
      queues: [sqsQueue],
    });

    queuePolicy.document.addStatements(
      new iam.PolicyStatement({
        sid: "VisualEditor0",
        effect: iam.Effect.ALLOW,
        principals: [glueRole],
        actions: ["sqs:*"],
        resources: ["*"]
      }),
      new iam.PolicyStatement({
        sid: "topic-subscription-arn:" + s3eventTopic.topicArn,
        effect: iam.Effect.ALLOW,
        principals: [new iam.ServicePrincipal('sns.amazonaws.com')],
        actions: ["sqs:SendMessage"],
        resources: [sqsQueue.queueArn],
        conditions: {
          "ArnLike": {"aws:SourceArn": s3eventTopic.topicArn}
        }
      }),
    );

    const glue_db = new glue_alpha.Database(this, 'SignalsDatabase', {
      databaseName: process.env.CDK_DEFAULT_ACCOUNT + '-signals-database',
    });

    new glue.CfnCrawler(this, 'SignalsCrawler', {
      name: process.env.CDK_DEFAULT_ACCOUNT + '-signals-crawler',
      role: glueRole.roleArn,
      databaseName: glue_db.databaseName,
      targets: {
        s3Targets: [{
          eventQueueArn: sqsQueue.queueArn,
          path: s3Bucket_signals.bucketName + '/raw_data',
        }]
      },
      recrawlPolicy: {
        recrawlBehavior: 'CRAWL_EVENT_MODE',
      },
    });

    // sns topic
    const logTopic = new sns.Topic(this, 'SignalsLogTopic', {
      topicName: 'signals-logs'
    });

    const lambdaRole = new iam.Role(this, 'SignalsLambdaRole', {
      roleName: process.env.CDK_DEFAULT_ACCOUNT + '-signals-lambda-role',
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
      description: 'SignalsLambdaRole',
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
        iam.ManagedPolicy.fromAwsManagedPolicyName('AmazonSNSFullAccess'),
      ]
    });

    // lambda
    const logLambda = new lambda.Function(this, 'SignalsLogLambda', {
      functionName: 'signals-error-notification',
      role: lambdaRole,
      runtime: lambda.Runtime.PYTHON_3_9,
      environment: {
        'SNS_TOPIC_ARN': logTopic.topicArn
      },
      code: lambda.Code.fromAsset('lambda'),
      handler: 'log_error.handler'
    });

    new logs.LogGroup(this, 'SignalsLambdaLogGroup', {
        logGroupName: `/aws/lambda/${logLambda.functionName}`,
        retention: logs.RetentionDays.ONE_WEEK,
        removalPolicy: cdk.RemovalPolicy.DESTROY
    });

    new logs.SubscriptionFilter(this, 'SignalsLambdaLoadGroupSubscription', {
      logGroup: loadLogGroup,
      destination: new destinations.LambdaDestination(logLambda),
      filterPattern: logs.FilterPattern.allTerms('ERROR'),
    });

    new logs.SubscriptionFilter(this, 'SignalsLambdaTransformGroupSubscription', {
      logGroup: transformLogGroup,
      destination: new destinations.LambdaDestination(logLambda),
      filterPattern: logs.FilterPattern.allTerms('ERROR'),
    });

    logLambda.addPermission('SignalCloudwatchPermission', {
      principal: new iam.ServicePrincipal('logs.amazonaws.com')
    });

  }
}