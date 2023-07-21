#!/usr/bin/env python3
import os

import aws_cdk as cdk

from stacks.challenge1_stack import Challenge1Stack


app = cdk.App()
Challenge1Stack(app, "Challenge1Stack")

app.synth()
