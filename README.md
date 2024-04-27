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

- [ ] Convert the pipeline to get the pdfs from the base level site with a standardized link of the format: https://www.mbp.state.md.us/bpqapp/Orders/{id}.PDF. Some of the links don't work because they are incorrect. Change this and create a system in the scraper that will not alter old data.
- [ ] Download any documents that got ignored in the pipeline the first time or did not exist
- [ ] Run new documents through the pipeline to get their text
- [ ] Edit the regular expressions to get better license and case numbers, possibly using the structure of them instead of recognizing the text
- [ ] Make a full pipeline from start to end that will run all the functions needed to keep the site updated
- [ ] Clean up the type of offense recorded, both from the result of it in the disciplinary action and from the documents themselves
- [ ] Start working on the look and layout of the main page. Want to have a header, a searchable function that will show types of offenses, etc., graphics and facet/sorting by the offense type
- [ ] 