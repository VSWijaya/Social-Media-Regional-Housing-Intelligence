# Social Media Regional Housing Intelligence

**Monash University · FIT3164 Data Science Project Part 2 · Team DS02**

Social Media Regional Housing Intelligence is a web dashboard that combines Reddit sentiment with Australian Bureau of Statistics (ABS) demographic data for ten Melbourne suburbs. It helps users compare how suburbs are discussed online alongside official demographic information.

The project brings together data collection, text preprocessing, topic categorisation, sentiment modelling and dashboard development. This repository contains the dashboard files, data preparation code, datasets and sentiment modelling work.

## What the dashboard provides

- Comparisons between selected Melbourne suburbs.
- Sentiment summaries derived from Reddit posts and comments.
- Topic-based insights into local experiences and concerns.
- ABS demographic information to give context to suburb comparisons.
- Keyword summaries to help users explore recurring discussion themes.

The dashboard is intended for people researching suburbs for housing and lifestyle decisions. It presents public perceptions alongside demographic information; it does not predict property prices.

## Suburb coverage

The project focuses on these ten Melbourne suburbs:

| Suburb | Suburb |
| --- | --- |
| Carlton | Clayton |
| Collingwood | Dandenong |
| Eaglemont | Nunawading |
| Oakleigh | Officer |
| Richmond | Vermont |

## Data sources

### Reddit discussions

Posts and comments relating to the selected suburbs provide the text used for sentiment analysis. Collection and preprocessing code is located in `scraper_and_preprocessing/`. The repository also includes the master datasets, cleaned data and a labelled training subset.

### ABS demographics

ABS data supplies demographic context for the suburb comparisons. These official statistics complement the discussion-based insights and should be interpreted according to their reference period and geographic coverage.

## Analysis workflow

1. **Collect suburb-related discussions.** Gather Reddit posts and comments associated with the target suburbs.
2. **Clean and organise the text.** Remove duplicates and unusable records, identify suburb mentions and prepare the text for analysis. Suburb attribution helps reduce the risk of assigning a discussion to the wrong location.
3. **Categorise discussion topics.** Group relevant content into themes such as affordability, crime and safety, lifestyle amenities, and education and employment.
4. **Prepare labelled data.** Use automated sentiment labelling to support model development, with review of ambiguous or inaccurate labels. These labels are approximate reference labels, rather than independently established ground truth.
5. **Develop and evaluate sentiment models.** Compare VADER with BERT, fine-tune BERT and evaluate predictions using held-out data.
6. **Prepare dashboard outputs.** Combine sentiment results, discussion summaries and ABS demographics for presentation in the web interface.

## Sentiment modelling

VADER was investigated as an initial baseline. The team then adopted BERT to meet the project's model fine-tuning requirement and compared its performance with VADER.

The modelling work included preparing labelled text, separating training and test data, fine-tuning the model and reviewing its predictions. The original accuracy target of more than 80% was not achieved.

Because automated labels were used during data preparation, evaluation results must be interpreted with care: agreement with an automated label does not necessarily establish that a prediction correctly captures the author's meaning. Sarcasm, mixed opinions and context-dependent language remained challenges.

## Repository contents

| File or folder | Purpose |
| --- | --- |
| `docs/` | Dashboard front-end files |
| `scraper_and_preprocessing/` | Data collection and preprocessing code |
| `ABS_2021_Melbourne_Suburb_Data.xlsx` | ABS 2021 demographic data for the selected suburbs |
| `FIT3164Model.ipynb` | Sentiment modelling notebook |
| `ModelWithTopics.py` | Python modelling code incorporating topics |
| `label_sentiment.py` | Automated sentiment labelling function |
| `LABELING_NOTES.txt` | Notes accompanying the labelled data |
| `clayton_sentiment_dataset.csv` | Clayton sample dataset used for initial model training |
| `melbourne_suburb_master_dataset_part1.csv`–`melbourne_suburb_master_dataset_part4.csv` | Master dataset split across four CSV files |
| `melbourne_suburb_cleaned.zip` | Cleaned data with empty or unusable rows removed |
| `melbourne_suburb_training_subset.csv` | Labelled training subset |
| `suburb_sentiment_summary.json` | Sentiment summary output for the dashboard |
| `mock_suburb_data.json` | Mock data used during front-end development |
| `requirements.txt` | Python dependency list |
| `S1_DS_02_Project proposal report.pdf` | Original project proposal |

## Working with the project

### Python dependencies

From the repository root, install the dependencies listed in `requirements.txt`:

```bash
python -m pip install -r requirements.txt
```

### Data preparation and modelling

- Refer to `scraper_and_preprocessing/` for the collection and preprocessing code.
- Use the supplied master datasets and cleaned archive when working with the collected data.
- Read `LABELING_NOTES.txt` alongside `melbourne_suburb_training_subset.csv` to understand the labelled data.
- Open `FIT3164Model.ipynb` in a Jupyter-compatible environment to inspect the modelling workflow. Check its input paths against the datasets available in your checkout before running cells.
- Refer to `ModelWithTopics.py` for the topic-related modelling code and `label_sentiment.py` for the sentiment labelling function.

### Dashboard files

The dashboard front-end is located in `docs/`. The repository includes `suburb_sentiment_summary.json` for sentiment summaries and `ABS_2021_Melbourne_Suburb_Data.xlsx` for demographic data. `mock_suburb_data.json` is a development fixture and should not be treated as an analysis result.

## Limitations

- **Coverage:** Analysis is limited to ten suburbs and the discussions collected for the project.
- **Representation:** Reddit users and discussions are not a representative sample of all residents. Discussion volume can also differ between suburbs.
- **Interpretation:** Sentiment reflects how people express opinions online. It is not an objective measure of suburb quality, safety or affordability.
- **Model quality:** Automated labels and sentiment predictions can contain errors, particularly for sarcasm, mixed sentiment and unclear suburb references.
- **Time and geography:** Historical discussions and ABS statistics may refer to different periods or geographic boundaries.
- **Updates:** The delivered project analyses collected data rather than providing continuous live Reddit monitoring.

## Future improvements

- Expand the manually reviewed sentiment dataset and evaluate against independent human labels.
- Improve handling of sarcasm, mixed opinions and discussions mentioning multiple suburbs.
- Increase coverage for suburbs with fewer relevant discussions.
- Extend suburb coverage and support repeatable data refreshes.
- Document the complete dashboard and model setup alongside the final source code and model assets.

## Academic context

Developed by Team DS02 for Monash University's FIT3164 Data Science Project Part 2. The completed project demonstrates a workflow from unstructured social media text to an interactive dashboard combining sentiment analysis with official demographic data.

## AI Acknowledgement
Priscilla:
ChatGPT (OpenAI) was used to help write the code for the Reddit data scraper and the data preprocessing pipeline.
ChatGPT (OpenAI) and Claude (Anthropic) were used to help write the frontend code).
Claude (Anthropic) was used to help write the code that improves the keyword extraction method.
I verified all AI-generated code by reviewing it, running it, and checking that the outputs were correct, and I made changes where needed.

Vincent: 
ChatGPT (OpenAI) was used to help write code for sentiment labelling, preparing the training and testing datasets, 
and comparing VADER and BERT. It was also used to help identify irrelevant stop words, improve the wording and structure of my 
report sections, and revise the project README. I reviewed and edited the generated text and checked the code and outputs, 
making changes where needed.

Fauzanda: 
Google Gemini AI Flash and Flash-Lite 3.6 was used to help write code for creating the model for sentiment scoring, starting from splitting the dataset, fine tuning, testing, generating the output, and etc. Pretty much, nearly all of the code and comments written is generated by AI. I always reviewed and revised the code generated by AI.
