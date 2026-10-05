import pandas as pd
import numpy as np
from transformers import pipeline

def save_custom_suburb_topic_matrix(
    csv_file, 
    suburbs, 
    topics, 
    topic_col='source_type', 
    output_csv='custom_suburb_topic_matrix.csv', 
    text_col='model_text', 
    max_chars=1500
):
    """
    Computes sentiment scores for specifically provided lists of suburbs and topics.
    Output columns structure: [suburb] + [Topic 1, Topic 2, ... Topic N] + [average_sentiment_score]
    """
    
    # 1. Load dataset
    df = pd.read_csv(csv_file)
    
    if 'suburb' not in df.columns or topic_col not in df.columns:
        raise ValueError(f"Dataset must contain 'suburb' and '{topic_col}' columns.")
    
    # 2. Initialize pre-trained Hugging Face sentiment pipeline
    pipe = pipeline(
        "sentiment-analysis", 
        model="cardiffnlp/twitter-roberta-base-sentiment-latest", 
        truncation=True, 
        max_length=512
    )
    
    # 3. Helper function to process individual texts via chunking
    def get_score(text):
        text_str = str(text)
        chunks = [text_str[i:i+max_chars] for i in range(0, len(text_str), max_chars)]
        chunk_scores = []
        
        for chunk in chunks:
            res = pipe(chunk)[0]
            label, conf = res['label'].lower(), res['score']
            
            if 'positive' in label:
                score = conf
            elif 'negative' in label:
                score = -conf
            else:
                score = 0.0
            chunk_scores.append(score)
            
        return np.mean(chunk_scores)

    matrix_data = []
    
    # 4. Iterate through your provided list of suburbs
    for sub in suburbs:
        sub_subset = df[df['suburb'].str.lower() == sub.lower()]
        row_data = {'suburb': sub}
        
        all_topic_scores = []
        
        # 5. Iterate through your provided list of topics (n columns)
        for topic in topics:
            # Filter rows matching both the suburb and the specific topic
            topic_subset = sub_subset[sub_subset[topic_col].astype(str).str.lower() == topic.lower()]
            
            if topic_subset.empty:
                row_data[topic] = None
            else:
                scores = topic_subset[text_col].apply(get_score)
                mean_topic_score = scores.mean()
                row_data[topic] = mean_topic_score
                all_topic_scores.extend(scores.tolist())
                
        # 6. Calculate overall average sentiment for this suburb (last column)
        if all_topic_scores:
            row_data['average_sentiment_score'] = np.mean(all_topic_scores)
        else:
            row_data['average_sentiment_score'] = None
            
        matrix_data.append(row_data)
        
    # 7. Convert to DataFrame and save to CSV
    result_df = pd.DataFrame(matrix_data)
    result_df.to_csv(output_csv, index=False)
    
    print(result_df)
    return result_df

if __name__ == "__main__":
    # Input 1: Your list of target suburbs
    target_suburbs = ['Carlton', 'Melbourne']
    
    # Input 2: Your list of target topics (e.g., source types, categories, or aspects)
    target_topics = ['Education']
    
    # Run the function
    save_custom_suburb_topic_matrix(
        csv_file='sample.csv', 
        suburbs=target_suburbs, 
        topics=target_topics,
        topic_col='source_type', # Change this if your topics are in a different column (e.g., 'aspect' or 'subreddit')
        output_csv='custom_suburb_topic_matrix.csv'
    )