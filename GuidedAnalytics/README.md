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


## What if I don't have Fabric, I don't have these sample tables, or I just want to use my data?  

Guided Analytics is pretty simple and it will work with any database.  

After you have your database wired up to the IDE and the LLM, do these prompts:

**Change these prompts according to your context**

```text
list the tables in my database/lakehouse/whatever
```

That will ensure you have a good wire up.  

Now try something like this:

```text
>Context:  
Look at my lakehouse.  You'll note I have 9 tables.  The data comes from a South American e-commerce company and the orders span approx 2016 to 2018.  You should assume the data is accurate but it's a good idea to verify any assumptions by actually querying the data.  

>Role:
You are a business analyst with 10 years of experience helping retailers and e-commerce companies improve their business processes.  You are starting a new consulting gig and you were given the above context about the data you want to use to help this company improve their business.  You have no additional information about this company.  

>Interview:

>I am the CEO of this company.  I want YOU to give me a list of FIVE potential research questions that you believe would be answerable given the datasets above.  After you give those to me I will pick a few with you and ask you to dive deeper.  

>Go!

_Note: we skipped the "Tasks:" section.  We'll do that after the LLM gives us the questions._
```

```text
>Task:  
>OK.  Let's look at this question:"What are the most popular product categories in terms of revenue, and how do their sales performance vary across different regions".  Can you give me a design of the analysis that would answer this question given the information provided?  Don't make assumptions about the data, what steps would you take to analyze the data at each step of the process?  Keep the process high level, I'll ask follow-on questions.  
```

## Key Takeaways

* Note how I wrote the prompts.  I want the LLM to query/discover the data with me, as if I were a new consultant.  
* We want the LLM to _think a metalayer higher_.  Don't give it a problem in this case, have IT give YOU a list of potential research topics.  
* _design of analysis_ is similar to _exploratory data analysis_.  These are terms in the data industry that experienced practitioners understand, and therefore the LLMs understand.  
* Tell the LLM never to make assumptions.  
* Tell the LLM we want to have conversations