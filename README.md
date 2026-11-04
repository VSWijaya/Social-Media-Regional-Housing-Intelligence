# Social Media Regional Housing Intelligence

**Monash University · FIT3164 Data Science Project Part 2 · Team DS02**

Social Media Regional Housing Intelligence is a web dashboard that combines Reddit sentiment with Australian Bureau of Statistics (ABS) demographic data for ten Melbourne suburbs. It helps users compare how suburbs are discussed online alongside official demographic information.

The project brings together data collection, text preprocessing, topic categorisation, sentiment modelling and dashboard development. This README describes the completed project and retains the original collection instructions for reference.

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

Posts and comments relating to the selected suburbs provide the text used for sentiment analysis. The original collection pipeline targeted `r/melbourne` and included suburb detection, cleaning, deduplication and topic categorisation.

The project initially planned to use the Reddit API. API access constraints led to an alternative collection approach during implementation. The API instructions below therefore describe the original collection scripts, rather than the final collection method.

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

## Original collection scripts

The uploaded Phase 1 README documents the following files. This list covers the original collection component, rather than the complete dashboard and modelling codebase.

| File | Purpose |
| --- | --- |
| `config.py` | Collection settings and suburb configuration |
| `reddit_collector.py` | Reddit API collection logic |
| `data_preprocessor.py` | Text cleaning, suburb detection and topic categorisation |
| `run_collection.py` | Collection and preprocessing entry point |
| `requirements.txt` | Python dependencies for the collection component |
| `.env.example` | Template for API credentials |

### Running the original API pipeline

These steps require the original scripts and approved Reddit API access. They do not launch the completed dashboard or run BERT training.

1. Install the collection dependencies from the directory containing `requirements.txt`:

   ```bash
   python -m pip install -r requirements.txt
   ```

2. Configure an application through [Reddit's application settings](https://www.reddit.com/prefs/apps), subject to the access requirements for your account.
3. Copy `.env.example` to `.env` and populate the credential fields expected by the scripts. Keep credentials out of version control.
4. Review the suburb list and collection settings in `config.py`.
5. Run the original collection entry point:

   ```bash
   python run_collection.py
   ```

### Collection outputs

| Path | Description |
| --- | --- |
| `data/raw/all_posts_raw.csv` | Raw collected posts |
| `data/raw/all_comments_raw.csv` | Raw collected comments |
| `data/processed/posts_processed.csv` | Cleaned posts with suburb and topic labels |
| `data/processed/comments_processed.csv` | Cleaned comments with suburb and topic labels |
| `data/processed/combined_for_analysis.csv` | Combined text dataset for subsequent sentiment analysis |

Dashboard startup instructions and BERT training commands depend on their respective source files and are not specified by the original collection README.

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
