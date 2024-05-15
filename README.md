# md_doc_discipline
Tracking Maryland's disciplined doctors

#### 2024-03-11

- [ ] Make sure requirements are installed
- [ ] Test scraper to make sure it works
- [ ] Install tesseract and other needed software for OCR
- [ ] Work on the assignment

#### 2024-03-13

Start to build the pipeline in ocr.sh by testing out the steps

- [ ] Make a directory to store the PDFs
- [ ] Download the PDFs from alerts.csv to that directory using [csvcut](https://csvkit.readthedocs.io/en/latest/tutorial/1_getting_started.html#csvcut-data-scalpel) 
- [ ] Use [pdf2image](https://pypi.org/project/pdf2image-cli/) to convert the PDFs to png files

#### 2024-03-25

- [ ] Make a directory to store text from the images
- [ ] Run tesseract on the images, saving the output in the text directory
- [ ] Stitch together the text files from each PDF into a single file

#### 2024-04-26 To Do

- [-] Convert the pipeline to get the pdfs from the base level site with a standardized link of the format: https://www.mbp.state.md.us/bpqapp/Orders/{id}.PDF. Some of the links don't work because they are incorrect. Change this and create a system in the scraper that will not alter old data.
- [-] Download any documents that got ignored in the pipeline the first time or did not exist
- [-] Run new documents through the pipeline to get their text
- [-] Edit the regular expressions to get better license and case numbers, possibly using the structure of them instead of recognizing the text
- [/] Make a full pipeline from start to end that will run all the functions needed to keep the site updated
- [ ] Clean up the type of offense recorded, both from the result of it in the disciplinary action and from the documents themselves
- [ ] Start working on the look and layout of the main page. Want to have a header, a searchable function that will show types of offenses, etc., graphics and facet/sorting by the offense type

#### 2024-04-27 Update

I am not as far as I would like to be, but I am trying to give myself some grace and celebrate what I have accomplished. Coding sometimes feels like a constant pattern of one step forward, three steps back and while that can be hard to deal with, it makes finding a solution much sweeter. I have set up the virtual environment to download and set up every package I need to run the pipeline and I have set up the pipeline using full_pipeline.sh, which references multiple other scripts. This week, I was able to do that and do some data cleaning to get license and case numbers for each case. I also planned out how users will be able to get around the site. My goal is to have two search functions at the top, one for doctor name and the other for type of incident. That search will also be connected to the full text of the document. I am going to try using [groq's API](https://console.groq.com/playground) to get key information out of the documents. I will standardize the incident types from there and use the data as part of the main page. The main page will also include the five most recent alerts with an option to click below that and see the full list of alerts, shown as either a database table or as a concatenated description of the alert and doctor. On the main page, I will also include some significant categorizations, including doctor type, incident type and year so that people can see the cases within those groupings as a data table when they click on each of them. I will make charts to go along with this, but I am not sure yet what software I will use since I want the data to consistently update.

For each doctor/incident, I will embed the links to the pdf documents if people want to see more information on the cases. This coming week, I want to work a lot on the design and functionality of the main page and the doctor pages. I have done little to no work on those and while I don't see it taking a super long time, I want to make sure I complete it before I become stressed out by it.

#### Final ReadMe

The README needs to include any links to deployed or public aspects of this project. In other words: if you have a public Datasette instance, website or Twitter account, it should be linked and described here. If you have a Slack element, you should describe that as well. If your "deployed" aspect is within codespaces, that's fine, just say that.

Your README will need to summarize, in no less than 750 words, your development efforts based on your project updates. This should be a write-through of those previous updates that removes duplicative language and provides updates (such as, "I had problem X and I solved it using Y"). You can link out to Google docs if needed, but the README must have at least an introduction and the links described above.

It also should contain a section on how you would deploy and maintain your app. This includes the use of continuous tools like GitHub Actions but also services such as GitHub Pages. For Slack-based apps, where/how are you keeping data stored (if at all)? Can users access some or all of the underlying data? In terms of maintenance, what's the appropriate schedule for updates and how will you know whether updates have been run correctly or not? Finally, when does this app outlive its usefulness? Is there a logical sunset date, or does it continue into perpetuity? Does the data outlive the app/bot, and if so, where?

Make sure that this summary isn't all sunshine and roses. I want to hear frustrations and limitations. Be honest - but be sure to acknowledge what you've accomplished, too.