import streamlit as st
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import sqlite3, hashlib, json, re
from pathlib import Path
from datetime import datetime, timezone

st.set_page_config(page_title='GuardianX Civic Records AI',page_icon='🛡️',layout='wide')
DB=Path(__file__).with_name('guardianx.db')

def connect():
    c=sqlite3.connect(DB)
    c.row_factory=sqlite3.Row
    c.execute('CREATE TABLE IF NOT EXISTS records (id INTEGER PRIMARY KEY, name TEXT, content TEXT, sha TEXT UNIQUE, created TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS reviews (id INTEGER PRIMARY KEY, record_id INTEGER, query TEXT, decision TEXT, note TEXT, created TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS audit (id INTEGER PRIMARY KEY, action TEXT, detail TEXT, created TEXT)')
    c.commit()
    return c

def now(): return datetime.now(timezone.utc).isoformat(timespec='seconds')
def audit(c,action,detail): c.execute('INSERT INTO audit(action,detail,created) VALUES (?,?,?)',(action,detail,now()));c.commit()

def rows(c,sql,args=()): return [dict(x) for x in c.execute(sql,args).fetchall()]


def ai_assisted_search(records, query):
    if not records or not query.strip():
        return []
    documents = [r["content"] for r in records]
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    matrix = vectorizer.fit_transform(documents + [query])
    scores = cosine_similarity(matrix[-1:], matrix[:-1]).flatten()
    return sorted(
        [(float(score), record) for score, record in zip(scores, records) if score > 0],
        key=lambda x: x[0], reverse=True
    )


c=connect()
st.markdown('''<style>.block-container{padding-top:2rem;max-width:1250px}h1{color:#143d58}.stButton button[kind=primary]{background:#146c84}</style>''',unsafe_allow_html=True)
st.title('🛡️ GuardianX Civic Records AI')
st.caption('CIVIC INNOVATION PROTOTYPE · SYNTHETIC DEMO DATA · HUMAN-LED REVIEW · NO GOVERNMENT INTEGRATION')
page=st.sidebar.radio('Workspace',['Overview','Records','Search Workspace','Human Review','Audit & Exports'])

if page=='Overview':
    st.subheader('Public records workflow — transparent by design')
    st.info('Prototype demonstration only. Keyword-based retrieval is not semantic or generative AI. Human reviewers retain all disclosure and exemption decisions.')
    a,b,d=st.columns(3)
    a.metric('Records',c.execute('SELECT COUNT(*) FROM records').fetchone()[0])
    b.metric('Review decisions',c.execute('SELECT COUNT(*) FROM reviews').fetchone()[0])
    d.metric('Audit events',c.execute('SELECT COUNT(*) FROM audit').fetchone()[0])
    st.markdown('**Two-minute demo path:** Records → Search Workspace → Human Review → Audit & Exports')
    if st.button('Load fictional demo record',type='primary'):
        content='''FICTIONAL DEMO RECORD — NOT AN OFFICIAL CITY DOCUMENT\nTransportation Planning Memo — GX-DEMO-011\nDate: October 2026\nTopic: Traffic safety and temporary road closures.\nThe fictional transportation team reviewed pedestrian crossings, school-zone safety, and proposed road closures during resurfacing work.\nPublic engagement feedback requested clearer detour signs, safer intersections, and advance notification of transportation planning meetings.\nThis sample is synthetic and contains no personal information.'''
        sha=hashlib.sha256(content.encode()).hexdigest()
        try:
            c.execute('INSERT INTO records(name,content,sha,created) VALUES (?,?,?,?)',('GX-DEMO-011.txt',content,sha,now()));c.commit();audit(c,'DEMO_LOAD','Added fictional transportation record');st.success('Demo record loaded.')
        except sqlite3.IntegrityError:st.info('Demo record already exists.')

elif page=='Records':
    st.subheader('Records library')
    up=st.file_uploader('Upload UTF-8 plain text records (.txt)',type=['txt'],accept_multiple_files=True)
    if up and st.button('Import selected files',type='primary'):
        added=0
        for f in up:
            data=f.getvalue()
            if len(data)>2_000_000:st.warning(f'{f.name}: over 2 MB, skipped');continue
            try:content=data.decode('utf-8')
            except UnicodeDecodeError:st.warning(f'{f.name}: not UTF-8, skipped');continue
            sha=hashlib.sha256(data).hexdigest()
            try:
                c.execute('INSERT INTO records(name,content,sha,created) VALUES (?,?,?,?)',(f.name,content,sha,now()));c.commit();audit(c,'UPLOAD',f.name);added+=1
            except sqlite3.IntegrityError:st.info(f'{f.name}: duplicate skipped')
        st.success(f'{added} record(s) imported')
    for r in rows(c,'SELECT * FROM records ORDER BY id DESC'):
        with st.expander(f"#{r['id']} · {r['name']}"):
            st.text(r['content'][:12000]);st.caption('SHA-256: '+r['sha'])


elif page=='Search Workspace':
    st.subheader('Search workspace')
    query=st.text_input('Search records',value='traffic safety road closures')
    mode=st.radio(
        'Search method',
        ['Keyword Search','AI-Assisted TF-IDF Search','Semantic AI Search'],
        horizontal=True
    )
    st.caption(
        'Semantic AI uses a pretrained embedding model. '
        'Results are suggestions, not disclosure decisions. '
        'Human review remains required.'
    )

    records=rows(c,'SELECT * FROM records ORDER BY id DESC')

    if query.strip() and records:
        found=[]

        if mode=='Semantic AI Search':
            from sentence_transformers import SentenceTransformer
            from sklearn.metrics.pairwise import cosine_similarity

            @st.cache_resource(show_spinner='Loading Semantic AI model...')
            def load_semantic_model():
                return SentenceTransformer(
                    'sentence-transformers/all-MiniLM-L6-v2'
                )

            with st.spinner('Analyzing document meaning...'):
                model=load_semantic_model()
                documents=[r['content'] for r in records]
                embeddings=model.encode(
                    [query]+documents,
                    convert_to_numpy=True,
                    normalize_embeddings=True
                )
                scores=cosine_similarity(
                    embeddings[:1],embeddings[1:]
                )[0]

                for score,r in zip(scores,records):
                    if float(score)>=0.20:
                        found.append((float(score),r,r['content'][:500]))

        elif mode=='AI-Assisted TF-IDF Search':
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity

            documents=[r['content'] for r in records]
            vectorizer=TfidfVectorizer(stop_words='english')
            matrix=vectorizer.fit_transform([query]+documents)
            scores=cosine_similarity(matrix[:1],matrix[1:])[0]

            for score,r in zip(scores,records):
                if float(score)>0:
                    found.append((float(score),r,r['content'][:500]))

        else:
            terms=set(re.findall(r'[a-z0-9]{3,}',query.lower()))
            for r in records:
                content=r['content']
                score=sum(
                    len(re.findall(r'\b'+re.escape(t)+r'\b',content.lower()))
                    for t in terms
                )
                if score:
                    found.append((float(score),r,content[:500]))

        found.sort(key=lambda x:x[0],reverse=True)
        st.write(f'**{len(found)} matching record(s)**')

        for score,r,snippet in found:
            with st.container(border=True):
                st.markdown(f"**{r['name']}** · Relevance score: {score:.3f}")
                st.text(snippet)
                if st.button('Send to human review',key=f"review_{r['id']}"):
                    st.session_state['selected_record']=r['id']
                    st.session_state['selected_query']=query
                    audit(c,'SEARCH',f"Method: {mode}; Query: {query}; Record: {r['id']}")
                    st.success('Selected. Open Human Review from the sidebar.')

        if not found:
            st.info('No matching records found. Try another query.')

    elif not records:
        st.warning('Load or upload a record first.')

elif page=='Human Review':
    st.subheader('Human review')
    records=rows(c,'SELECT id,name FROM records ORDER BY id DESC')
    if not records:st.warning('Load or upload a record first.')
    else:
        ids=[r['id'] for r in records];selected=st.session_state.get('selected_record',ids[0]);idx=ids.index(selected) if selected in ids else 0
        rid=st.selectbox('Record',ids,index=idx,format_func=lambda i:next(r['name'] for r in records if r['id']==i))
        r=dict(c.execute('SELECT * FROM records WHERE id=?',(rid,)).fetchone())
        st.text_area('Source text',r['content'],height=190,disabled=True)
        with st.form('review'):
            q=st.text_input('Request / search context',value=st.session_state.get('selected_query','traffic safety road closures transportation planning'))
            decision=st.radio('Reviewer decision',['Include','Exclude','Needs further review'],horizontal=True)
            note=st.text_area('Reviewer rationale (required)')
            if st.form_submit_button('Save human decision',type='primary'):
                if not note.strip():st.error('Add a review note before saving.')
                else:
                    c.execute('INSERT INTO reviews(record_id,query,decision,note,created) VALUES (?,?,?,?,?)',(rid,q,decision,note.strip(),now()));c.commit();audit(c,'REVIEW',f'Record #{rid}: {decision}');st.success('Decision saved with audit event.')
    st.markdown('**Saved decisions**')
    st.dataframe(pd.DataFrame(rows(c,'SELECT * FROM reviews ORDER BY id DESC')),hide_index=True,use_container_width=True)

elif page=='Audit & Exports':
    st.subheader('Audit & exports')
    reviews=rows(c,'SELECT * FROM reviews ORDER BY id')
    events=rows(c,'SELECT * FROM audit ORDER BY id')
    x,y=st.columns(2);x.metric('Decisions to export',len(reviews));y.metric('Recorded events',len(events))
    st.markdown('**Reviewer decisions**')
    st.dataframe(pd.DataFrame(reviews),hide_index=True,use_container_width=True)
    st.markdown('**Audit trail**')
    st.dataframe(pd.DataFrame(events),hide_index=True,use_container_width=True)
    st.download_button('Download review decisions (JSON)',json.dumps(reviews,indent=2).encode(),'guardianx_reviews.json','application/json')
    st.download_button('Download review decisions (CSV)',pd.DataFrame(reviews,columns=['id','record_id','query','decision','note','created']).to_csv(index=False).encode(),'guardianx_reviews.csv','text/csv')
    st.download_button('Download audit events (JSON)',json.dumps(events,indent=2).encode(),'guardianx_audit.json','application/json')

st.divider()
st.caption('GuardianX LLC · Prototype only · Fictional records · Human oversight required · Not a government system')
