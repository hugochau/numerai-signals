import * as cdk from 'aws-cdk-lib';
import { SignalsStack } from '../lib/signals-stack';
import { SignalsPipelineStack } from '../lib/signals-pipeline-stack';

const app = new cdk.App();
new SignalsStack(app, 'SignalsStack');
// new SignalsPipelineStack(app, 'SignalsPipelineStack');