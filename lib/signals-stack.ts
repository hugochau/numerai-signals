import * as ec2 from "aws-cdk-lib/aws-ec2";
import * as ecs from "aws-cdk-lib/aws-ecs";
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as glue from 'aws-cdk-lib/aws-glue';
import * as glue_alpha from '@aws-cdk/aws-glue-alpha'
import * as cdk from 'aws-cdk-lib';
import * as events from 'aws-cdk-lib/aws-events';
import * as targets from 'aws-cdk-lib/aws-events-targets';
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
      memoryLimitMiB: 8192,
      cpu: 1024,
      taskRole: taskRole,
      runtimePlatform: {
        operatingSystemFamily: ecs.OperatingSystemFamily.LINUX,
        cpuArchitecture: ecs.CpuArchitecture.ARM64,
      },
    });

    // create container image
    // load
    fargateTaskDefinitionLoad.addContainer("SignalsContainerLoad", {
      image: ecs.ContainerImage.fromAsset("./docker/load"),
      logging: ecs.LogDrivers.awsLogs({ streamPrefix: 'signals', logRetention: 30 })
    });

    // transform
    fargateTaskDefinitionTransform.addContainer("SignalsContainerTransform", {
      image: ecs.ContainerImage.fromAsset("./docker/transform"),
      logging: ecs.LogDrivers.awsLogs({ streamPrefix: 'signals', logRetention: 30 })
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
      schedule: events.Schedule.cron({hour: '*/12', minute: '0'}),
      targets: [eventRuleTargetLoad],
    });

    new events.Rule(this, 'SignalsRuleTransform', {
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
  }
}