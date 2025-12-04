# Vibe Analytics
Vibe analytics:  advancing self-service analytics


Exploratory Data Analytics
EDA involves manually exploring, visualizing, and summarizing data to
understand its various aspects.  The goal would be to do this when you don't understand the data or **want to ensure you aren't injecting your biases into the data**.  LLMs can really help here.  Most folks really struggle with EDA.  You have to follow a process.  LLMs and vibe coding can help you adhere to a good framework for doing this.  

 It helps in identifying patterns, detecting
inconsistencies, testing assumptions, and gaining insights.

EDA also involves like data
cleaning, handling missing values, outlier detection, and
feature engineering. This work is cumbersome and error-prone, even for the best data scientists and engineers.  LLMs to the rescue!


What is the typical data structure for data
coming from <some_business_ area>?
What data quality problems should I test for in
the DataFrame I have provided you?
What distribution should I expect in the column
describing <some_activity>?
How
do
I
deal
with
<a_clear_description_of_the_encountered_probl
em>?

## Guided Analytics

When we are unfamiliar with a dataset, or even unfamiliar with the _analytics process_, we can use **Guided Analytics** and an LLM to help us out.  

_When to use?_

If you are a business person and are unfamiliar with the data, or you have familiarity with the data, but you are looking for some novel questions to ask of the data, this technique is for you.  

[Before we look at the demo, we need to load some data into Fabric]()

[Let's look at a demo]()

We are going to use the [CRIT Prompting Method](https://www.linkedin.com/pulse/context-role-interview-task-crit-framework-unlocking-ais-eric-shreve-0znkc/) **which works really well** for Guided Analytics.  

## Here is the prompt:

>Context:  
I have the following set of data in my datalake arranged into the following tables with some annotations.  The data comes from a South American company and the orders span approx 2016 to 2018.  You should assume the data is accurate but you should NOT make assumptions about the data schema or even the data quality.  

>Role:
You are a business analyst with 10 years of experience helping retailers and e-commerce companies improve their business processes.  You are starting a new consulting gig and you were given the above context about the data you want to use to help this company improve their business.  You have no additional information about this company.  

>Interview:

>I am the CEO of this company.  I want YOU to give me a list of FIVE potential research questions that you believe would be answerable given the datasets above.  After you give those to me I will pick a few with you and ask you to dive deeper.  

>Go!

_Note: we skipped the "Tasks:" section.  We'll do that after the LLM gives us the questions._

Here is the output I got on my machine:

```text
Here are some research questions that might be interesting:

1. What is the impact of delivery time (actual vs. estimated)
on customer satisfaction and review scores?
2. What is the relationship between product attributes (e.g.,
weight, dimensions) and overhead costs (e.g., shipping
costs)?
...

```

Once you found a question that looks interesting, we can dive in with "the Task"

>Task:  
>OK.  Let's look at this question:"What are the most popular product categories in terms of revenue, and how do their sales performance vary across different regions".  Can you give me a design of the analysis that would answer this question given the information provided?  Don't make assumptions about the data, what steps would you take to analyze the data at each step of the process?  Keep the process high level, I'll ask follow-on questions.  

Here is the output I got on my machine:

```text

Here are the steps I would take:

1. Data Preparation
We need to ensure the tables can be joined to each other.  There are issues with
...
2. Check Data Quality
    * handle missing values
    * convert datatypes
    * create new data attributes (such as "deliveryTime" = Arrived-Shipped)
...
3. Exploratory Data Analysis
    * compute summary statistics and determine if they look reasonable.
    * create visualizations
    * correlation analysis:  look at bivariate and trivariate analysis
...
4. Summary, Interpretation, Discussion
    * Summarize key findings
    * What might explain differences from observed and expected outcomes?
    * Discuss the potential limitations of the findings and data.  
5. Provide Prescriptive Recommendations
```
This looks EXACTLY like the process a good data scientist SHOULD be following.  

...Continuing...





