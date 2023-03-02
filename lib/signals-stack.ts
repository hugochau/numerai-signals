import * as ec2 from "aws-cdk-lib/aws-ec2";
import * as ecs from "aws-cdk-lib/aws-ecs";
import * as s3 from "aws-cdk-lib/aws-s3";
import * as iam from "aws-cdk-lib/aws-iam";
import * as glue from "aws-cdk-lib/aws-glue";
import * as glue_alpha from "@aws-cdk/aws-glue-alpha";
import * as cdk from "aws-cdk-lib";
import * as events from "aws-cdk-lib/aws-events";
import * as targets from "aws-cdk-lib/aws-events-targets";
import * as sns from "aws-cdk-lib/aws-sns";
import * as s3n from "aws-cdk-lib/aws-s3-notifications";
import * as sqs from "aws-cdk-lib/aws-sqs";
import * as subscriptions from "aws-cdk-lib/aws-sns-subscriptions";
import * as logs from "aws-cdk-lib/aws-logs";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as destinations from "aws-cdk-lib/aws-logs-destinations";
import { Construct } from "constructs";

export class SignalsStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    /*
    A cluster where we will deploy our tasks
    objects created:
      - EC2 vpc
      - ECS cluster
    */
    const vpc = new ec2.Vpc(this, "SignalsVpc", {
      vpcName: process.env.CDK_DEFAULT_ACCOUNT + "-signals-vpc",
      maxAzs: 2,
      natGateways: 0,
      subnetConfiguration: [
        {
          // 'subnetType' controls Internet access, as described above.
          subnetType: ec2.SubnetType.PUBLIC,
          name: "Public",
          cidrMask: 24,
        },
      ],
    });

    // create cluster for our tasks
    const cluster = new ecs.Cluster(this, "SignalsCluster", {
      clusterName: process.env.CDK_DEFAULT_ACCOUNT + "-signals-cluster",
      vpc: vpc,
    });

    /*
    The tasks we deploy to our cluster
    objects created:
      - IAM Role: a role to control tasks, assumed by ServicePrincipal ecs-tasks
      - Task definitions: architecture type
      - Cloudwatch log groups: to persist log tasks runs
    */
    // create role for our tasks
    const taskRole = new iam.Role(this, "SignalsTaskRole", {
      roleName: process.env.CDK_DEFAULT_ACCOUNT + "-signals-task-role",
      assumedBy: new iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
      description: "IAM role for our tasks",
      // inlinePolicies: {
      //   DescribeACMCerts: describeAcmCertificates,
      // },
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName("AdministratorAccess"),
      ],
    });

    // create task definitions
    // signals-load
    const fargateTaskDefinitionLoad = new ecs.FargateTaskDefinition(
      this,
      "SignalsTaskDefLoad",
      {
        family: "signals-load",
        memoryLimitMiB: 8192,
        cpu: 1024,
        taskRole: taskRole,
        runtimePlatform: {
          operatingSystemFamily: ecs.OperatingSystemFamily.LINUX,
          cpuArchitecture: ecs.CpuArchitecture.ARM64,
        },
      }
    );

    // signals-transform
    const fargateTaskDefinitionTransform = new ecs.FargateTaskDefinition(
      this,
      "SignalsTaskDefTransform",
      {
        family: "signals-transform",
        memoryLimitMiB: 8192,
        cpu: 1024,
        taskRole: taskRole,
        runtimePlatform: {
          operatingSystemFamily: ecs.OperatingSystemFamily.LINUX,
          cpuArchitecture: ecs.CpuArchitecture.ARM64,
        },
      }
    );

    // create log group
    // signals-transform
    const loadLogGroup = new logs.LogGroup(this, "SignalsLogLoad", {
      logGroupName: `/aws/fargate/${fargateTaskDefinitionLoad.family}`,
      retention: 30,
    });

    const transformLogGroup = new logs.LogGroup(this, "SignalsLogTransform", {
      logGroupName: `/aws/fargate/${fargateTaskDefinitionTransform.family}`,
      retention: 30,
    });

    // create container image
    // signals-load
    fargateTaskDefinitionLoad.addContainer("SignalsContainerLoad", {
      containerName: fargateTaskDefinitionLoad.family,
      image: ecs.ContainerImage.fromAsset("./docker/load"),
      logging: ecs.LogDrivers.awsLogs({
        streamPrefix: "signals",
        logGroup: loadLogGroup,
      }),
    });

    // signals-transform
    fargateTaskDefinitionTransform.addContainer("SignalsContainerTransform", {
      containerName: fargateTaskDefinitionTransform.family,
      image: ecs.ContainerImage.fromAsset("./docker/transform"),
      logging: ecs.LogDrivers.awsLogs({
        streamPrefix: "signals",
        logGroup: transformLogGroup,
      }),
    });

    /*
    We trigger our tasks periodically using cron events
    objects created:
      - events targets
      - events rules
    */
    // targets
    const eventRuleTargetLoad = new targets.EcsTask({
      cluster: cluster,
      taskDefinition: fargateTaskDefinitionLoad,
      subnetSelection: { subnetType: ec2.SubnetType.PUBLIC },
      taskCount: 1,
    });

    const eventRuleTargetTransform = new targets.EcsTask({
      cluster: cluster,
      taskDefinition: fargateTaskDefinitionTransform,
      subnetSelection: { subnetType: ec2.SubnetType.PUBLIC },
      taskCount: 1,
    });

    // cron rules
    new events.Rule(this, "SignalsRuleLoad", {
      ruleName: process.env.CDK_DEFAULT_ACCOUNT + "-signals-load-cron",
      schedule: events.Schedule.cron({ hour: "23", minute: "0" }),
      targets: [eventRuleTargetLoad],
    });

    new events.Rule(this, "SignalsRuleTransform", {
      ruleName: process.env.CDK_DEFAULT_ACCOUNT + "-signals-transform-cron",
      schedule: events.Schedule.cron({
        weekDay: "SAT",
        hour: "1",
        minute: "0",
      }),
      targets: [eventRuleTargetTransform],
    });

    /*
    We need S3 buckets to store data
    objects created:
      - s3 bucket to store raw/processed data
      - s3 bucket to store athena query outputs
    */

    // signals-data
    const s3Bucket_signals = new s3.Bucket(this, "SignalsRawDataBucket", {
      bucketName: process.env.CDK_DEFAULT_ACCOUNT + "-signals-data",
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      // encryption: s3.BucketEncryption.S3_MANAGED,
    });

    // athena
    new s3.Bucket(this, "SignalsAthenaBucket", {
      bucketName: process.env.CDK_DEFAULT_ACCOUNT + "-athena",
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
    });

    /*
    A Glue crawler publishing raw data to a DB that we will query with Athena
    A S3 event notification pipeline to trigger crawler on folder updates.
    objects created:
      - S3 event notification for our signals-data bucket
      - SNS topic to receive and deliver S3 event notifications
      - A policy for the SNS topic
      - SQS queue to store messages
      - A policy for the SQS
      - Policies for the crawler
      - IAM Role for the crawler
      - A Glue crawler
      - A Glue database
    */

    // sns topic
    const s3eventTopic = new sns.Topic(this, "SignalsS3EventsTopic", {
      topicName: "signals-s3-events",
    });

    // policy for the sns topic
    const topicPolicy = new sns.TopicPolicy(
      this,
      "SignalsS3EventsTopicPolicy",
      {
        topics: [s3eventTopic],
      }
    );

    topicPolicy.document.addStatements(
      new iam.PolicyStatement({
        sid: "s3_to_sns_events_stmt_1",
        effect: iam.Effect.ALLOW,
        principals: [new iam.ServicePrincipal("s3.amazonaws.com")],
        actions: ["sns:Publish"],
        resources: [s3eventTopic.topicArn],
        conditions: {
          StringEquals: {
            "aws:SourceAccount": process.env.CDK_DEFAULT_ACCOUNT,
          },
          ArnLike: {
            "aws:SourceArn": "arn:aws:s3:*:*:" + s3Bucket_signals.bucketName,
          },
        },
      })
    );

    // s34 event notification
    s3Bucket_signals.addEventNotification(
      s3.EventType.OBJECT_CREATED,
      // publish to sns
      new s3n.SnsDestination(s3eventTopic),
      // filter only raw_data folder
      { prefix: "raw_data" }
    );

    // policies for the glue role
    // s3 policy
    // for 
    const crawlerS3Policy = new iam.ManagedPolicy(
      this,
      "SignalsCrawlerS3Policy",
      {
        managedPolicyName: "signals-glue-crawler-s3-policy",
        document: new iam.PolicyDocument({
          statements: [
            new iam.PolicyStatement({
              effect: iam.Effect.ALLOW,
              actions: ["s3:GetObject", "s3:PutObject"],
              resources: [
                "arn:aws:s3:::" + s3Bucket_signals.bucketName + "/raw_data/*",
              ],
            }),
          ],
        }),
      }
    );

    // sqs policy
    const crawlerSQSPolicy = new iam.ManagedPolicy(
      this,
      "SignalsCrawlerSQSPolicy",
      {
        managedPolicyName: "signals-glue-crawler-sqs-policy",
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
                "sqs:SetQueueAttributes",
              ],
              resources: [
                "arn:aws:sqs:eu-west-1:" +
                  process.env.CDK_DEFAULT_ACCOUNT +
                  ":" +
                  s3eventTopic.topicName,
              ],
            }),
          ],
        }),
      }
    );

    const glueRole = new iam.Role(this, "SignalsGlueRole", {
      roleName: process.env.CDK_DEFAULT_ACCOUNT + "-signals-glue-role",
      assumedBy: new iam.ServicePrincipal("glue.amazonaws.com"),
      description: "SignalsGlueRole",
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName(
          "service-role/AWSGlueServiceRole"
        ),
        crawlerS3Policy,
        crawlerSQSPolicy,
      ],
    });

    // sqs queue
    const sqsQueue = new sqs.Queue(this, "SignalsQueue", {
      queueName: "signals-s3-events",
    });

    // add sns subscription
    s3eventTopic.addSubscription(new subscriptions.SqsSubscription(sqsQueue));

    // policy for the sqs queue
    const queuePolicy = new sqs.QueuePolicy(this, "SignalsQueuePolicy", {
      queues: [sqsQueue],
    });

    queuePolicy.document.addStatements(
      new iam.PolicyStatement({
        sid: "VisualEditor0",
        effect: iam.Effect.ALLOW,
        principals: [glueRole],
        actions: ["sqs:*"],
        resources: ["*"],
      }),
      new iam.PolicyStatement({
        sid: "topic-subscription-arn:" + s3eventTopic.topicArn,
        effect: iam.Effect.ALLOW,
        principals: [new iam.ServicePrincipal("sns.amazonaws.com")],
        actions: ["sqs:SendMessage"],
        resources: [sqsQueue.queueArn],
        conditions: {
          ArnLike: { "aws:SourceArn": s3eventTopic.topicArn },
        },
      })
    );

    // DB to store metadata
    const glue_db = new glue_alpha.Database(this, "SignalsDatabase", {
      databaseName: process.env.CDK_DEFAULT_ACCOUNT + "-signals-database",
    });

    // crawler
    new glue.CfnCrawler(this, "SignalsCrawler", {
      name: process.env.CDK_DEFAULT_ACCOUNT + "-signals-crawler",
      role: glueRole.roleArn,
      databaseName: glue_db.databaseName,
      targets: {
        s3Targets: [
          {
            eventQueueArn: sqsQueue.queueArn,
            path: s3Bucket_signals.bucketName + "/raw_data",
          },
        ],
      },
      recrawlPolicy: {
        recrawlBehavior: "CRAWL_EVENT_MODE",
      },
    });

    /*
    An email delivery system should any task fail
    objects created:
      - SNS topic that delivers messages to subscribers
      - A lambda function for parsing log on error
      - A role for our lambda
      - A subscription filter for each task we defined
    */

      // sns topic
    const logTopic = new sns.Topic(this, "SignalsLogTopic", {
      topicName: "signals-logs",
    });

    // role for the parsing lambda
    const lambdaRole = new iam.Role(this, "SignalsLambdaRole", {
      roleName: process.env.CDK_DEFAULT_ACCOUNT + "-signals-lambda-role",
      assumedBy: new iam.ServicePrincipal("lambda.amazonaws.com"),
      description: "SignalsLambdaRole",
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName(
          "service-role/AWSLambdaBasicExecutionRole"
        ),
        iam.ManagedPolicy.fromAwsManagedPolicyName("AmazonSNSFullAccess"),
      ],
    });

    // lambda function to parse error logs
    const logLambda = new lambda.Function(this, "SignalsLogLambda", {
      functionName: "signals-error-notification",
      role: lambdaRole,
      runtime: lambda.Runtime.PYTHON_3_9,
      environment: {
        SNS_TOPIC_ARN: logTopic.topicArn,
      },
      code: lambda.Code.fromAsset("lambda"),
      handler: "log_error.handler",
    });

    // a log group to store lambda logs
    new logs.LogGroup(this, "SignalsLambdaLogGroup", {
      logGroupName: `/aws/lambda/${logLambda.functionName}`,
      retention: logs.RetentionDays.ONE_WEEK,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // log subscription filters
    // signals-load task
    new logs.SubscriptionFilter(this, "SignalsLambdaLoadGroupSubscription", {
      logGroup: loadLogGroup,
      destination: new destinations.LambdaDestination(logLambda),
      // send notification only if log contains keyword ERROR
      filterPattern: logs.FilterPattern.allTerms("ERROR"),
    });

    // signals-transform task
    new logs.SubscriptionFilter(
      this,
      "SignalsLambdaTransformGroupSubscription",
      {
        logGroup: transformLogGroup,
        destination: new destinations.LambdaDestination(logLambda),
        filterPattern: logs.FilterPattern.allTerms("ERROR"),
      }
    );

    // permission for lambda to access log
    logLambda.addPermission("SignalCloudwatchPermission", {
      principal: new iam.ServicePrincipal("logs.amazonaws.com"),
    });
  }
}
