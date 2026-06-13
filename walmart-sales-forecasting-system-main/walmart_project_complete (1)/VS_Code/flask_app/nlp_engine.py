

import re
import math
from collections import Counter

try:
    import nltk
    from nltk.tokenize import word_tokenize
    from nltk.stem import PorterStemmer
    from nltk.corpus import stopwords

    for resource in ['punkt', 'punkt_tab', 'stopwords']:
        try:
            nltk.data.find(f'tokenizers/{resource}' if 'punkt' in resource else f'corpora/{resource}')
        except LookupError:
            nltk.download(resource, quiet=True)

    NLTK_AVAILABLE = True
    STOP_WORDS = set(stopwords.words('english'))
    stemmer = PorterStemmer()
except ImportError:
    NLTK_AVAILABLE = False
    STOP_WORDS = set()
    stemmer = None

try:
    from groq import Groq
    GROQ_API_KEY = "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"
    groq_client = Groq(api_key=GROQ_API_KEY)
    GROQ_AVAILABLE = True
    print("[OK] Groq LLM API initialized successfully")
except Exception as e:
    GROQ_AVAILABLE = False
    groq_client = None
    print(f"[WARNING] Groq API not available: {e}")

def preprocess(text):
    """Tokenize, lowercase, remove stopwords, and stem the text using NLTK."""
    text = text.lower().strip()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)

    if NLTK_AVAILABLE:
        tokens = word_tokenize(text)
        tokens = [stemmer.stem(t) for t in tokens if t not in STOP_WORDS and len(t) > 1]
    else:

        basic_stops = {'the','a','an','is','are','was','were','be','been','being',
                       'have','has','had','do','does','did','will','would','could',
                       'should','may','might','shall','can','of','in','to','for',
                       'with','on','at','from','by','about','as','into','through',
                       'during','before','after','above','below','between','out',
                       'off','over','under','again','further','then','once','it',
                       'its','this','that','these','those','i','me','my','we','our',
                       'you','your','he','him','his','she','her','they','them','their',
                       'what','which','who','whom','when','where','how','and','but',
                       'or','nor','not','no','so','if'}
        tokens = [w for w in text.split() if w not in basic_stops and len(w) > 1]

    return tokens

def extract_entities(text):
    """Extract store numbers, department numbers, and other entities from query."""
    entities = {
        'stores': [],
        'departments': [],
        'months': [],
        'top_n': None,
        'comparison': False
    }

    text_lower = text.lower()

    store_patterns = [
        r'store\s*(?:#|number|no\.?)?\s*(\d+)',
        r'stores?\s+(\d+(?:\s*(?:,|and)\s*\d+)*)',
    ]
    for pattern in store_patterns:
        matches = re.findall(pattern, text_lower)
        for m in matches:
            nums = re.findall(r'\d+', m if isinstance(m, str) else str(m))
            entities['stores'].extend([int(n) for n in nums])

    dept_patterns = [
        r'(?:dept|department)\s*(?:#|number|no\.?)?\s*(\d+)',
        r'(?:dept|department)s?\s+(\d+(?:\s*(?:,|and)\s*\d+)*)',
    ]
    for pattern in dept_patterns:
        matches = re.findall(pattern, text_lower)
        for m in matches:
            nums = re.findall(r'\d+', m if isinstance(m, str) else str(m))
            entities['departments'].extend([int(n) for n in nums])

    month_map = {
        'january': 1, 'february': 2, 'march': 3, 'april': 4,
        'may': 5, 'june': 6, 'july': 7, 'august': 8,
        'september': 9, 'october': 10, 'november': 11, 'december': 12,
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4,
        'jun': 6, 'jul': 7, 'aug': 8, 'sep': 9,
        'oct': 10, 'nov': 11, 'dec': 12
    }
    for name, num in month_map.items():
        if name in text_lower:
            entities['months'].append(num)

    top_match = re.search(r'top\s*(\d+)', text_lower)
    if top_match:
        entities['top_n'] = int(top_match.group(1))

    if any(w in text_lower for w in ['compare', 'versus', 'vs', 'difference', 'between']):
        entities['comparison'] = True

    return entities

INTENT_TEMPLATES = {
    'top_stores': [
        'which store has the highest sales',
        'best performing store',
        'top stores by sales',
        'highest selling store',
        'best store',
        'top store performance',
        'which store sells the most',
        'leading stores',
        'store ranking',
    ],
    'top_departments': [
        'which department has the highest sales',
        'best performing department',
        'top departments by sales',
        'highest selling department',
        'best department',
        'top department performance',
        'leading departments',
        'department ranking',
    ],
    'worst_stores': [
        'which store has the lowest sales',
        'worst performing store',
        'bottom stores',
        'lowest selling store',
        'underperforming stores',
        'store with least sales',
    ],
    'worst_departments': [
        'which department has the lowest sales',
        'worst performing department',
        'bottom departments',
        'lowest selling department',
        'underperforming departments',
    ],
    'holiday_impact': [
        'what is the holiday impact on sales',
        'holiday vs regular sales',
        'how do holidays affect sales',
        'holiday effect',
        'holiday sales difference',
        'sales during holidays',
        'impact of holidays',
        'do holidays increase sales',
    ],
    'store_details': [
        'tell me about store',
        'store details',
        'store information',
        'show store data',
        'store stats',
        'give me store info',
        'how is store performing',
        'store performance',
    ],
    'department_details': [
        'tell me about department',
        'department details',
        'department information',
        'show department data',
        'department stats',
        'give me department info',
        'how is department performing',
    ],
    'seasonal_trend': [
        'seasonal trend',
        'monthly sales trend',
        'which month has highest sales',
        'best month for sales',
        'worst month for sales',
        'seasonal pattern',
        'monthly pattern',
        'sales by month',
        'when are sales highest',
    ],
    'overall_summary': [
        'give me a summary',
        'overall summary',
        'project overview',
        'total sales',
        'how much total sales',
        'summary of data',
        'general statistics',
        'data overview',
        'tell me about the data',
    ],
    'store_comparison': [
        'compare store',
        'store comparison',
        'difference between stores',
        'store vs store',
        'compare two stores',
        'which store is better',
    ],
    'store_type_analysis': [
        'store type analysis',
        'type a vs type b',
        'compare store types',
        'which store type is best',
        'performance by store type',
        'store types',
    ],
    'help': [
        'help',
        'what can you do',
        'what questions can i ask',
        'how to use',
        'guide me',
        'commands',
        'options',
    ],
}

def _build_vocab():
    """Build vocabulary and IDF weights from intent templates."""
    doc_freq = Counter()
    all_docs = []

    for intent, phrases in INTENT_TEMPLATES.items():
        for phrase in phrases:
            tokens = preprocess(phrase)
            all_docs.append(tokens)
            unique_tokens = set(tokens)
            for t in unique_tokens:
                doc_freq[t] += 1

    n_docs = len(all_docs)
    idf = {}
    for term, freq in doc_freq.items():
        idf[term] = math.log((n_docs + 1) / (freq + 1)) + 1                

    return idf, all_docs

IDF_WEIGHTS, ALL_TEMPLATE_DOCS = _build_vocab()

def _tfidf_vector(tokens):
    """Compute TF-IDF vector for a list of tokens."""
    tf = Counter(tokens)
    total = len(tokens) if tokens else 1
    vector = {}
    for t in tf:
        tf_val = tf[t] / total
        idf_val = IDF_WEIGHTS.get(t, 1.0)
        vector[t] = tf_val * idf_val
    return vector

def _cosine_similarity(v1, v2):
    """Compute cosine similarity between two sparse vectors (dicts)."""
    common = set(v1.keys()) & set(v2.keys())
    dot = sum(v1[k] * v2[k] for k in common)
    norm1 = math.sqrt(sum(val ** 2 for val in v1.values())) if v1 else 0
    norm2 = math.sqrt(sum(val ** 2 for val in v2.values())) if v2 else 0
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)

def classify_intent(query_text):
    """Classify the user's query into an intent using TF-IDF cosine similarity."""
    query_tokens = preprocess(query_text)
    if not query_tokens:
        return 'help', 0.0

    query_vec = _tfidf_vector(query_tokens)

    best_intent = 'help'
    best_score = 0.0

    for intent, phrases in INTENT_TEMPLATES.items():
        for phrase in phrases:
            template_tokens = preprocess(phrase)
            template_vec = _tfidf_vector(template_tokens)
            score = _cosine_similarity(query_vec, template_vec)
            if score > best_score:
                best_score = score
                best_intent = intent

    return best_intent, best_score

def _get_data_summary(full_data):
    """Build a concise data summary string to send to Groq as context."""
    try:
        total_stores = int(full_data['Store'].nunique())
        total_depts = int(full_data['Dept'].nunique())
        total_records = len(full_data)
        total_sales = float(full_data['Weekly_Sales'].sum())
        avg_sales = float(full_data['Weekly_Sales'].mean())
        date_min = full_data['Date'].min().strftime('%Y-%m-%d')
        date_max = full_data['Date'].max().strftime('%Y-%m-%d')

        top_5_stores = full_data.groupby('Store')['Weekly_Sales'].mean().nlargest(5)
        top_5_str = ", ".join([f"Store {int(s)}: ${v:,.0f}/week" for s, v in top_5_stores.items()])

        bottom_3_stores = full_data.groupby('Store')['Weekly_Sales'].mean().nsmallest(3)
        bottom_3_str = ", ".join([f"Store {int(s)}: ${v:,.0f}/week" for s, v in bottom_3_stores.items()])

        top_5_depts = full_data.groupby('Dept')['Weekly_Sales'].mean().nlargest(5)
        top_depts_str = ", ".join([f"Dept {int(d)}: ${v:,.0f}/week" for d, v in top_5_depts.items()])

        holiday_avg = float(full_data[full_data['IsHoliday'] == True]['Weekly_Sales'].mean())
        regular_avg = float(full_data[full_data['IsHoliday'] == False]['Weekly_Sales'].mean())

        if 'Type' in full_data.columns:
            type_stats = full_data.groupby('Type')['Weekly_Sales'].mean()
            type_str = ", ".join([f"Type {t}: ${v:,.0f}/week" for t, v in type_stats.items()])
        else:
            type_str = "N/A"

        summary = (
            f"Walmart Sales Dataset: {total_stores} stores, {total_depts} departments, "
            f"{total_records:,} records from {date_min} to {date_max}. "
            f"Total Sales: ${total_sales:,.0f}. Avg Weekly Sales: ${avg_sales:,.0f}. "
            f"Top 5 Stores: {top_5_str}. "
            f"Bottom 3 Stores: {bottom_3_str}. "
            f"Top 5 Departments: {top_depts_str}. "
            f"Holiday Avg: ${holiday_avg:,.0f}, Regular Avg: ${regular_avg:,.0f}. "
            f"Store Types: {type_str}."
        )
        return summary
    except Exception:
        return "Walmart sales dataset with multiple stores, departments, and weekly sales records."


def _ask_groq(query_text, data_answer, data_summary):
    """Send the user query + data answer to Groq LLM for AI-enhanced insight."""
    if not GROQ_AVAILABLE or groq_client is None:
        return None

    try:
        system_prompt = (
            "You are a Walmart Sales Data Analyst AI. You analyze sales data and provide "
            "deep, actionable business insights. You have access to the following dataset summary:\n\n"
            f"{data_summary}\n\n"
            "Rules:\n"
            "- Be concise (max 4-5 sentences)\n"
            "- Provide analytical insight, not just repeat the data\n"
            "- Explain WHY a trend might exist (business reasoning)\n"
            "- Suggest actionable recommendations when relevant\n"
            "- Use dollar amounts and percentages from the data provided"
        )

        user_prompt = (
            f"User Question: {query_text}\n\n"
            f"Data Answer (from our database):\n{data_answer}\n\n"
            "Now provide a brief AI analytical insight about this data. "
            "Explain the business significance and any patterns you notice."
        )

        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.4,
            max_tokens=300,
            top_p=0.9
        )

        ai_text = response.choices[0].message.content.strip()
        return ai_text

    except Exception as e:
        print(f"[WARNING] Groq API call failed: {e}")
        return None


def generate_response(query_text, data_context):
    """
    Main NLP pipeline (enhanced with Groq AI):
    1. Preprocess the query (NLTK tokenization, stemming)
    2. Extract entities (store/dept numbers via regex)
    3. Classify intent using TF-IDF + Cosine Similarity
    4. Generate data-driven response from Pandas
    5. Enhance with Groq LLM analytical insight

    Args:
        query_text: The natural language question
        data_context: dict with 'full_data', 'train_data', etc.
    Returns:
        dict with 'answer', 'ai_insight', 'intent', 'confidence', 'entities', 'nlp_steps'
    """
    import numpy as np

    full_data = data_context.get('full_data')
    if full_data is None:
        return {
            'answer': 'Sorry, the sales data is not loaded. Please check the database connection.',
            'ai_insight': None,
            'intent': 'error',
            'confidence': 0,
            'entities': {},
            'nlp_steps': [],
            'groq_used': False
        }

    tokens = preprocess(query_text)

    entities = extract_entities(query_text)

    intent, confidence = classify_intent(query_text)

    if confidence < 0.15:
        if entities['stores'] and not entities['departments']:
            intent = 'store_details'
            confidence = 0.5
        elif entities['departments'] and not entities['stores']:
            intent = 'department_details'
            confidence = 0.5
        elif entities['comparison']:
            intent = 'store_comparison'
            confidence = 0.5

    nlp_steps = [
        f"Tokenization: {tokens}",
        f"Entities Found: Stores={entities['stores']}, Depts={entities['departments']}",
        f"Intent: {intent} (confidence: {confidence:.2f})"
    ]

    answer = _build_answer(intent, entities, full_data, query_text)

    ai_insight = None
    groq_used = False
    if GROQ_AVAILABLE and intent != 'help':
        data_summary = _get_data_summary(full_data)
        ai_insight = _ask_groq(query_text, answer, data_summary)
        if ai_insight:
            groq_used = True
            nlp_steps.append("Groq LLM: AI analytical insight generated")

    return {
        'answer': answer,
        'ai_insight': ai_insight,
        'intent': intent,
        'confidence': round(confidence, 3),
        'entities': {
            'stores': entities['stores'],
            'departments': entities['departments'],
            'months': entities['months'],
            'top_n': entities['top_n'],
        },
        'nlp_steps': nlp_steps,
        'groq_used': groq_used
    }

def _build_answer(intent, entities, full_data, original_query):
    """Build a human-readable answer based on the classified intent."""
    import numpy as np

    top_n = entities.get('top_n', 5) or 5

    try:
        if intent == 'top_stores':
            top = full_data.groupby('Store')['Weekly_Sales'].mean().nlargest(top_n)
            lines = [f"Top {top_n} Stores by Average Weekly Sales:"]
            for rank, (store, avg) in enumerate(top.items(), 1):
                lines.append(f"  {rank}. Store {int(store)} — ${avg:,.2f} avg/week")
            return '\n'.join(lines)

        elif intent == 'top_departments':
            top = full_data.groupby('Dept')['Weekly_Sales'].mean().nlargest(top_n)
            lines = [f"Top {top_n} Departments by Average Weekly Sales:"]
            for rank, (dept, avg) in enumerate(top.items(), 1):
                lines.append(f"  {rank}. Department {int(dept)} — ${avg:,.2f} avg/week")
            return '\n'.join(lines)

        elif intent == 'worst_stores':
            bottom = full_data.groupby('Store')['Weekly_Sales'].mean().nsmallest(top_n)
            lines = [f"Bottom {top_n} Stores by Average Weekly Sales:"]
            for rank, (store, avg) in enumerate(bottom.items(), 1):
                lines.append(f"  {rank}. Store {int(store)} — ${avg:,.2f} avg/week")
            return '\n'.join(lines)

        elif intent == 'worst_departments':
            bottom = full_data.groupby('Dept')['Weekly_Sales'].mean().nsmallest(top_n)
            lines = [f"Bottom {top_n} Departments by Average Weekly Sales:"]
            for rank, (dept, avg) in enumerate(bottom.items(), 1):
                lines.append(f"  {rank}. Department {int(dept)} — ${avg:,.2f} avg/week")
            return '\n'.join(lines)

        elif intent == 'holiday_impact':
            regular = full_data[full_data['IsHoliday'] == False]['Weekly_Sales']
            holiday = full_data[full_data['IsHoliday'] == True]['Weekly_Sales']
            reg_avg = regular.mean()
            hol_avg = holiday.mean()
            lift = ((hol_avg - reg_avg) / reg_avg) * 100

            return (
                f"Holiday Impact Analysis:\n"
                f"  Regular Week Avg: ${reg_avg:,.2f}\n"
                f"  Holiday Week Avg: ${hol_avg:,.2f}\n"
                f"  Holiday Lift: {lift:+.2f}%\n"
                f"  Regular Weeks: {len(regular):,}\n"
                f"  Holiday Weeks: {len(holiday):,}\n"
                f"\nHolidays {'increase' if lift > 0 else 'decrease'} sales by {abs(lift):.1f}% on average."
            )

        elif intent == 'store_details':
            store_ids = entities['stores']
            if not store_ids:

                total = full_data['Store'].nunique()
                avg = full_data.groupby('Store')['Weekly_Sales'].mean().mean()
                return f"There are {total} stores in the dataset with an overall average weekly sales of ${avg:,.2f}. Ask about a specific store (e.g., 'Tell me about store 20')."

            results = []
            for sid in store_ids[:3]:                   
                sd = full_data[full_data['Store'] == sid]
                if sd.empty:
                    results.append(f"Store {sid}: No data found.")
                    continue
                stype = sd['Type'].iloc[0] if 'Type' in sd.columns else 'N/A'
                size = int(sd['Size'].iloc[0]) if 'Size' in sd.columns else 0
                results.append(
                    f"Store {sid} (Type {stype}, Size {size:,} sqft):\n"
                    f"  Avg Weekly Sales: ${sd['Weekly_Sales'].mean():,.2f}\n"
                    f"  Total Sales: ${sd['Weekly_Sales'].sum():,.2f}\n"
                    f"  Departments: {sd['Dept'].nunique()}\n"
                    f"  Data Points: {len(sd):,}\n"
                    f"  Best Week: ${sd['Weekly_Sales'].max():,.2f}\n"
                    f"  Worst Week: ${sd['Weekly_Sales'].min():,.2f}"
                )
            return '\n\n'.join(results)

        elif intent == 'department_details':
            dept_ids = entities['departments']
            if not dept_ids:
                total = full_data['Dept'].nunique()
                avg = full_data.groupby('Dept')['Weekly_Sales'].mean().mean()
                return f"There are {total} departments in the dataset with an overall average weekly sales of ${avg:,.2f}. Ask about a specific department (e.g., 'Show me department 7')."

            results = []
            for did in dept_ids[:3]:
                dd = full_data[full_data['Dept'] == did]
                if dd.empty:
                    results.append(f"Department {did}: No data found.")
                    continue
                results.append(
                    f"Department {did}:\n"
                    f"  Avg Weekly Sales: ${dd['Weekly_Sales'].mean():,.2f}\n"
                    f"  Total Sales: ${dd['Weekly_Sales'].sum():,.2f}\n"
                    f"  Active in Stores: {dd['Store'].nunique()}\n"
                    f"  Data Points: {len(dd):,}\n"
                    f"  Best Week: ${dd['Weekly_Sales'].max():,.2f}\n"
                    f"  Worst Week: ${dd['Weekly_Sales'].min():,.2f}"
                )
            return '\n\n'.join(results)

        elif intent == 'seasonal_trend':
            monthly = full_data.copy()
            monthly['Month'] = monthly['Date'].dt.month
            trend = monthly.groupby('Month')['Weekly_Sales'].mean()
            month_names = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

            lines = ["Monthly Sales Trend:"]
            best_month = trend.idxmax()
            worst_month = trend.idxmin()

            for m in range(1, 13):
                if m in trend.index:
                    bar_len = int((trend[m] / trend.max()) * 20)
                    bar = '#' * bar_len
                    marker = ' << BEST' if m == best_month else (' << LOWEST' if m == worst_month else '')
                    lines.append(f"  {month_names[m-1]:>3}: ${trend[m]:>10,.2f}  {bar}{marker}")

            lines.append(f"\nBest Month: {month_names[best_month-1]} (${trend[best_month]:,.2f})")
            lines.append(f"Worst Month: {month_names[worst_month-1]} (${trend[worst_month]:,.2f})")
            return '\n'.join(lines)

        elif intent == 'overall_summary':
            total_sales = full_data['Weekly_Sales'].sum()
            avg_sales = full_data['Weekly_Sales'].mean()
            stores = full_data['Store'].nunique()
            depts = full_data['Dept'].nunique()
            records = len(full_data)
            date_min = full_data['Date'].min().strftime('%Y-%m-%d')
            date_max = full_data['Date'].max().strftime('%Y-%m-%d')

            return (
                f"Walmart Sales Dataset Summary:\n"
                f"  Total Stores: {stores}\n"
                f"  Total Departments: {depts}\n"
                f"  Total Records: {records:,}\n"
                f"  Date Range: {date_min} to {date_max}\n"
                f"  Total Sales: ${total_sales:,.2f}\n"
                f"  Average Weekly Sales: ${avg_sales:,.2f}\n"
                f"  Max Weekly Sales: ${full_data['Weekly_Sales'].max():,.2f}\n"
                f"  Min Weekly Sales: ${full_data['Weekly_Sales'].min():,.2f}"
            )

        elif intent == 'store_comparison':
            store_ids = entities['stores']
            if len(store_ids) < 2:
                return "Please specify two stores to compare (e.g., 'Compare store 1 and store 20')."

            s1, s2 = store_ids[0], store_ids[1]
            d1 = full_data[full_data['Store'] == s1]
            d2 = full_data[full_data['Store'] == s2]

            if d1.empty or d2.empty:
                return f"Data not found for one or both stores ({s1}, {s2})."

            avg1, avg2 = d1['Weekly_Sales'].mean(), d2['Weekly_Sales'].mean()
            diff = ((avg1 - avg2) / avg2) * 100

            return (
                f"Store Comparison: Store {s1} vs Store {s2}\n"
                f"\n  {'Metric':<25} {'Store '+str(s1):>15} {'Store '+str(s2):>15}\n"
                f"  {'─'*55}\n"
                f"  {'Avg Weekly Sales':<25} ${avg1:>14,.2f} ${avg2:>14,.2f}\n"
                f"  {'Total Sales':<25} ${d1['Weekly_Sales'].sum():>14,.2f} ${d2['Weekly_Sales'].sum():>14,.2f}\n"
                f"  {'Max Weekly Sales':<25} ${d1['Weekly_Sales'].max():>14,.2f} ${d2['Weekly_Sales'].max():>14,.2f}\n"
                f"  {'Departments':<25} {d1['Dept'].nunique():>15} {d2['Dept'].nunique():>15}\n"
                f"  {'Data Points':<25} {len(d1):>15,} {len(d2):>15,}\n"
                f"\nStore {s1} averages {abs(diff):.1f}% {'more' if diff > 0 else 'less'} than Store {s2}."
            )

        elif intent == 'store_type_analysis':
            type_stats = full_data.groupby('Type')['Weekly_Sales'].agg(['mean', 'count', 'sum'])
            lines = ["Store Type Analysis:"]
            for stype, row in type_stats.iterrows():
                n_stores = full_data[full_data['Type'] == stype]['Store'].nunique()
                lines.append(
                    f"  Type {stype}: {n_stores} stores, "
                    f"Avg ${row['mean']:,.2f}/week, "
                    f"Total ${row['sum']:,.2f}"
                )
            best = type_stats['mean'].idxmax()
            lines.append(f"\nBest performing type: {best} with ${type_stats.loc[best, 'mean']:,.2f} avg weekly sales.")
            return '\n'.join(lines)

        elif intent == 'help':
            return (
                "I can answer questions about the Walmart sales data. Try asking:\n\n"
                "  - 'Which store has the highest sales?'\n"
                "  - 'Top 10 departments by sales'\n"
                "  - 'Tell me about store 20'\n"
                "  - 'Show me department 7 details'\n"
                "  - 'Compare store 1 and store 4'\n"
                "  - 'What is the holiday impact on sales?'\n"
                "  - 'Monthly sales trend'\n"
                "  - 'Which store type performs best?'\n"
                "  - 'Give me an overall summary'\n"
                "  - 'Bottom 5 stores'\n"
                "  - 'Worst performing departments'"
            )

        else:
            return (
                "I'm not sure I understand that question. Here are some things you can ask:\n\n"
                "  - 'Which store has the highest sales?'\n"
                "  - 'Tell me about store 4'\n"
                "  - 'Compare store 1 and store 20'\n"
                "  - 'Holiday impact on sales'\n"
                "  - 'Monthly sales trend'\n"
                "  - 'Overall summary'\n\n"
                "Type 'help' for a full list of queries."
            )

    except Exception as e:
        return f"An error occurred while processing your query: {str(e)}"
