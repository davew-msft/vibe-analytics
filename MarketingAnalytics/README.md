

The data can be found here:  https://raw.githubusercontent.com/davew-msft/vibe-analytics/refs/heads/main/MarketingAnalytics/surveys.csv

**Adjust all prompts according to your needs and environment**

Start with this prompt:

```text
I have a csv of demo data available here:  https://raw.githubusercontent.com/davew-msft/vibe-analytics/refs/heads/main/MarketingAnalytics/surveys.csv

Please load it to a table in my database called dbo.marketing_surveys
```

Then ...

```text
Context:

Here is my business problem.  We just held a c suite meeting to discuss our marketing strategy.  Our CMO made this statement:  

> "Last quarter was the best quarter in our history. We crushed Wall Streets earning targets by a wide margin. I am POSITIVE that the key reason was our revamped digital advertising campaigns. Recently we conducted a comprehensive survey of our social media usage at our mall stores and it is apparent our Instagram presence is expanding.  52% of survey respondents said they learned about our company from Instagram.  We should double down on our Instagram ads to continue our earnings trajectory."

Everyone in the room, including me, was skeptical.  But we need hard data and analytics to prove it.  

Role:  
You are a marketing analytics data scientist with 10 years of experience in the retail space.  I want you to help me look through the data and, using your intuition and experience, help me understand if the CMO's statements are correct.  

Interview:  
I am the CEO of this retailer.  I want you to interview me and let's look at this data together.  I want YOU to ask me questions about my business, goals, etc, and let's reason through this problem together.  Feel free to ask me any questions that may help you dive deeper and offer better recommendations.  Work with me in a step-wise manner.  Let's look at each step together.  Assume I know nothing about data, analytics, and what a data scientist is or does.  

Task:
Should we invest more money in Instagram ad spend?  Or something else?  How much should we spend on Instagram ads?  Tell me what you are thinking at each step of the process and ask any follow-on questions as needed.  

The survey data is in a Microsoft Fabric table in a lakehouse attached to this notebook called "dbo.marketing_surveys".  I'm not sure what's in this table, but this is the data our CMO gave to us.  
```

You should see it do some amazing analytics.  

You WILL need a follow-on prompt during the interview.  Something like this should work:  

```text
Let me answer your initial questions:  

1.  "My gut feelings about the CMO's claim?"  I don't believe it.  It seems too good to be true.  
2. "Beyond just revenue, what matters most to you as CEO?  CLV, CAC, margins?"  Good questions!  These are things I haven't thought of.  For now, let's just focus on the "marketing claims".  

I'm glad you found that "52% is accurate, but misleading".  It's closer to 11% when we look at the data from the perspective YOU just showed me.  YOU JUST PROVED that I should be skeptical.  It's a "percent of a percent" problem.  I didn't think of that.  

Other questions you posed:  

* Whether we should look for additional data sources
  * let's not worry about this...YET.  
* What specific analyses to run next
  * Keep exploring the data with me and let's see if we can uncover anything else?  
* Whether Instagram really deserves more investment
  * Let's focus on this.  But I'm still mostly concerned with the existing survey data.  What else can you tell me.  
* What the RIGHT marketing strategy should be
  * Yes, we'll get to that soon Copilot.  

```


Then, something like this:

```text
Let me answer your questions and give you some additional context to consider:

* my apologies for the data quality issues.  I doublechecked and the "20-Dec" data is an anomaly and a data quality issue.  My data people are idiots and they didn't load the data correctly.
  * "20-Dec" should really be "12-20" for the "AgeBracket".  
  * Can you do me a favor?  It's going to take my data engineers another 6 months on a backlog to fix the data.  Can you just assume, for now that `"20-Dec" = 12-20` for the AgeBracket?  
* A little more about our business may help you.  
  * We are a retailer of **cold weather apparel** sold to mostly to the **Under 40** demographic.  
  * we are omni-channel but only about 20% of our receipts are from our shopping mall stores.  

I also just confirmed some things with the CMO about HOW her team conducted the interviews.  Here's the key findings:
* as indicated in the data, the surveys were only conducted on the days and times indicated in the data file.  I wonder what day of the week that was?  
* the surveys were only taken at one mall location in California.  
* the surveys were conducted **as the shoppers where leaving the store**
* in many cases the respondents would not give their actual age ranges and the folks conducting the surveys guessed at their age ranges.  
* the survey looked like this:  

Store Survey
1. Did you hear about us through social media?  Yes/No
2. If you answered "yes", which social media website?  

With this new information, can you provide any additional insights?  

```

## Key Takeaways 

* The LLM should pick up on a lot of problems with this data.
* The survey design is wrong
* All surveys were done on one day (a Tuesday) in summer (and we sell cold weather gear), during the day when our target demographic is at work, at a mall location when only 20% of our business comes from malls.  This is just a start.  It will likely find other issues.  
