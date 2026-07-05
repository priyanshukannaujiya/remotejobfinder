# Master Every Technology: Data Engineering Job Hunter (Volume 2)

Welcome back! In Volume 1, we covered Python, Web Scraping, and AI. 
In **Volume 2**, we will dive into the core backend infrastructure: **Databases, Core Data Engineering Concepts, Pandas, and Email Systems**.

---

# 4. Database

## 4.1 SQLite vs PostgreSQL & SQLAlchemy

**What is it?**  
SQLite is a lightweight, file-based relational database. SQLAlchemy is an Object-Relational Mapper (ORM), a Python library that lets you interact with a database using Python classes instead of raw SQL queries.

**Why do we need it?**  
We need a place to persist scraped jobs so we don't process or email the exact same job twice. Without a database, the pipeline would be stateless and highly inefficient.

**Why is it better than alternatives?**  
- *SQLite vs PostgreSQL*: PostgreSQL is a massive client-server database. SQLite is just a local file (`jobs.db`). For a personal bot processing thousands of jobs, SQLite is perfect, fast, and requires zero setup. If this scaled to multiple concurrent users, we would switch to Postgres.
- *SQLAlchemy vs sqlite3 (Raw SQL)*: SQLAlchemy allows us to write database-agnostic code. If we ever switch from SQLite to Postgres, we don't have to rewrite a single line of SQL.

**How does it work internally?**  
When we define `class Job(Base):` in SQLAlchemy, we map a Python class to a database table. When we do `db.add(job)`, SQLAlchemy dynamically generates the `INSERT INTO jobs...` SQL query, binds the parameters safely (preventing SQL injection), and executes it over a database connection pool.

**How is it used inside THIS project?**  
Check `job_hunter/database/models.py`. We define the schema (columns, types, constraints). In `job_hunter/database/db.py`, we use a `SessionLocal` to open a transaction, check for duplicates (using `in_()`), and insert new records.

**Industry Usage**  
Airbnb and LinkedIn use massive distributed databases (Cassandra, Snowflake, Postgres). However, SQLAlchemy is the absolute industry standard ORM for Python. Companies like Yelp heavily rely on it for their backend services.

**Interview Questions**  
- *Beginner*: What is an ORM?
- *Intermediate*: How does SQLite differ from Postgres in terms of concurrency (locking)?
- *Advanced*: Explain SQLAlchemy Connection Pooling and the Session lifecycle.

**Practical Example**  
```python
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String)

engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()
session.add(User(name="Alice"))
session.commit()
```

**Common Mistakes**  
*Mistake*: Forgetting to call `session.commit()` or `session.rollback()` inside a `try...except` block, leaving the database locked.
*Correction*: Always use a context manager or `try/finally: db.close()` pattern as seen in our `db.py`.

---

# 5. Data Engineering Concepts

## 5.1 ETL vs ELT & Data Pipelines

**What is it?**  
- **ETL (Extract, Transform, Load)**: Pull data, clean/enrich it in memory, then load it into the database.
- **ELT (Extract, Load, Transform)**: Pull raw data, dump it into a massive Data Warehouse, and use heavy SQL to transform it later.

**Why do we need it?**  
Raw scraped data is messy. Titles are capitalized weirdly, salaries are hidden in text, and tracking parameters pollute URLs.

**Why is it better than alternatives?**  
Our project uses **ETL**. We Extract (Scrape), Transform (Clean URLs, use LLM to score), and Load (save to SQLite). For this scale, ETL is cheaper and faster than setting up an ELT pipeline in Snowflake.

**How is it used inside THIS project?**  
`main_job.py` is the pipeline orchestrator. 
1. **Extract**: `scraper.fetch_jobs()`
2. **Transform**: `DataCleaner.clean_jobs()` & `LLMProcessor.process_jobs()`
3. **Load**: `db_manager.save_jobs()`

**Industry Usage**  
Netflix and Uber deal with petabytes of data, so they heavily use ELT with tools like dbt and Snowflake. However, the foundational pipeline orchestration (Airflow, Dagster) works exactly like our `main_job.py`.

**Interview Questions**  
- *Beginner*: What does ETL stand for?
- *Intermediate*: Why is data deduplication important before loading into a database?
- *Advanced*: When would you choose ELT over ETL?

---

# 6. Pandas

## 6.1 DataFrames & Vectorization

**What is it?**  
Pandas is a fast, powerful data manipulation library. The `DataFrame` is essentially a programmatic Excel spreadsheet.

**Why do we need it?**  
In `DataCleaner.py`, we need to find duplicates across hundreds of dictionaries, uppercase company names, and remove HTML tags. Doing this with standard Python `for` loops is slow and tedious.

**Why is it better than alternatives?**  
Pandas is built on top of NumPy (C backend), making it exponentially faster than Python lists (`Vectorization`). Alternatives like Polars or PySpark are used for massive datasets (gigabytes+), but Pandas is king for MB-sized data.

**How does it work internally?**  
Pandas operations don't loop over rows one by one. They apply C-level operations across entire columns simultaneously in memory.

**How is it used inside THIS project?**  
In `job_hunter/processors/data_cleaner.py`, we load raw dictionaries into a DataFrame, use `.drop_duplicates(subset=['company', 'title'])`, and use `.str.replace()` to strip HTML across all rows instantly.

**Industry Usage**  
Every Data Scientist at Google or Amazon uses Pandas for exploratory data analysis (EDA) and data cleaning.

**Interview Questions**  
- *Beginner*: What is a Pandas DataFrame?
- *Intermediate*: How do you handle missing values (NaN) in Pandas?
- *Advanced*: What is Vectorization and why is it faster than `.apply()`?

---

# 7. Email Systems

## 7.1 SMTP & MIME

**What is it?**  
SMTP (Simple Mail Transfer Protocol) is the internet standard for sending emails. MIME (Multipurpose Internet Mail Extensions) allows us to send HTML, attachments (CSV), and non-text data via email.

**Why do we need it?**  
The user needs to be notified immediately when a "Dream Job" is found.

**How does it work internally?**  
Python opens a TCP connection to `smtp.gmail.com` on Port 587. It initiates a `STARTTLS` handshake to encrypt the connection. It logs in, constructs the MIME payload, and transmits it to the Gmail servers to route to the recipient.

**How is it used inside THIS project?**  
In `job_hunter/email/sender.py`, we build a `MIMEMultipart` message, attach a beautiful HTML string, and optionally attach the `jobs.csv` file.

**Best Practices applied in our recent refactor**: We added `timeout=10` to the SMTP connection to ensure network hiccups don't permanently hang the pipeline.

---

*This concludes Volume 2. When you are ready, ask for Volume 3, which will cover Streamlit, Docker, GitHub Actions, Project Architecture, and the complete Code Walkthrough.*
