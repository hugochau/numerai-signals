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
import * as logs from 'aws-cdk-lib/aws-logs';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as destinations from 'aws-cdk-lib/aws-logs-destinations';
import { Construct } from 'constructs';
import { addToDeadLetterQueueResourcePolicy } from "aws-cdk-lib/aws-events-targets";


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
        // {
        //   cidrMask: 24,
        //   name: 'Application',
        //   subnetType: ec2.SubnetType.PRIVATE_WITH_NAT,
        // },
        // {
        //   cidrMask: 24,
        //   name: 'Private',
        //   subnetType: ec2.SubnetType.PRIVATE_ISOLATED,
        //   // reserved: true
        // }
      ],
    });

    // create cluster for our tasks
    const cluster = new ecs.Cluster(this, "SignalsCluster", {
      clusterName: process.env.CDK_DEFAULT_ACCOUNT + '-signals-cluster',
      vpc: vpc
    });

    // create ACM Permission Policy
    // const describeAcmCertificates = new iam.PolicyDocument({
    //   statements: [
    //     new iam.PolicyStatement({
    //       resources: ['arn:aws:acm:*:*:certificate/*'],
    //       actions: ['acm:DescribeCertificate'],
    //     }),
    //   ],
    // });

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

    // create service
    // new ecs.FargateService(this, 'SignalsService', {
    //   cluster: cluster,
    //   taskDefinition: fargateTaskDefinitionLoad,
    //   assignPublicIp: true,
    //   desiredCount: 0
    // });

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

    const glueRole = new iam.Role(this, 'SignalsGlueRole', {
      roleName: process.env.CDK_DEFAULT_ACCOUNT + '-signals-glue-role',
      assumedBy: new iam.ServicePrincipal('glue.amazonaws.com'),
      description: 'SignalsGlueRole',
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSGlueServiceRole'),
        iam.ManagedPolicy.fromAwsManagedPolicyName('AmazonS3FullAccess'),
      ]
    });

    const glue_db = new glue_alpha.Database(this, 'SignalsDatabase', {
      databaseName: process.env.CDK_DEFAULT_ACCOUNT + '-signals-database',
    });

    new glue.CfnCrawler(this, 'SignalsCrawler', {
      name: process.env.CDK_DEFAULT_ACCOUNT + '-signals-crawler',
      role: glueRole.roleArn,
      databaseName: glue_db.databaseName,
      targets: {
        s3Targets: [{
          // connectionName: 'connectionName',
          // dlqEventQueueArn: 'dlqEventQueueArn',
          // eventQueueArn: 'eventQueueArn',
          // exclusions: ['exclusions'],
          path: s3Bucket_signals.bucketName + '/raw_data',
          // sampleSize: 123,
        }]
      }
    });

    // sns topic
    const topic = new sns.Topic(this, 'SignalsTopic', {
      topicName: 'SignalsTopic'
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
        'SNS_TOPIC_ARN': topic.topicArn
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