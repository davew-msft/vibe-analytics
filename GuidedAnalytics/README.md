## Guided Analytics

When we are unfamiliar with a dataset, or even unfamiliar with the analytics process, we can use Guided Analytics and an LLM to help us out.

When to use?

If you are a business person and are unfamiliar with the data, or you have familiarity with the data, but you are looking for some novel questions to ask of the data, this technique is for you.

## CRIT Prompting

We are going to use the [CRIT Prompting Method](https://www.linkedin.com/pulse/context-role-interview-task-crit-framework-unlocking-ais-eric-shreve-0znkc/), which works really well for Vibe/Guided Analytics.  

What is CRIT prompting?  It's an iterative prompting technique researchers have found works very well to get higher-quality results.  A `CRIT Prompt` consists of sections:
* Context:  background information the LLM needs to set the stage
* Role:  the "persona" or role that the LLM will play.  This further informs the LLM how it should behave and interact with you
* Interview:  your "persona" or role.  We tell the LLM that it should interact with you in an "interview-style".  You will ask additional clarifying questions and you inform the LLM to do likewise.  
* Task(s):  What you want the LLM to do.  

## Getting Data

For this demo, we need to get some sample data.  [Kaggle has a good ecommerce sample dataset](https://www.kaggle.com/api/v1/datasets/download/olistbr/brazilian-ecommerce) we can use.  You likely know nothing about it, that's good.  

Or, use your own data that's already loaded into Fabric.  

[If you want to load the data, follow these steps](data-loading.md)

## Let's do the Analytics with the CRIT Prompts.  

From the Fabric UI:
* create a new spark notebook
* click the `Open with vscode` option near the top right.  
* [Follow along using my notebook](./GuidedAnalytics.ipynb) (or upload it to your workspace)