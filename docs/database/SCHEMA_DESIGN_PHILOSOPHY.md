# Relational Schema Design Philosophy

## 1. Core Principles

1. **Strict Relational Integrity for Core Hierarchy**:
   The educational structure (`Course → Subject → Chapter → Lecture`) represents canonical pedagogical knowledge. Using strict relational foreign keys (`ON DELETE CASCADE`) prevents orphaned content and guarantees that deletions or updates propagate cleanly without dead references.

2. **Zero Binary Blobs in PostgreSQL**:
   Database tables store strictly text, numbers, dates, UUIDs, and JSON metadata. Heavy video binaries, PDF lecture notes, and student homework photos reside entirely in external object storage. The database stores only the immutable S3 storage key (e.g., `s3_key: "submissions/hw-04/student-12/photo_1.jpg"`).

3. **Pragmatic Use of JSONB**:
   PostgreSQL `JSONB` is used for polymorphic or dynamic structures that do not warrant complex join tables:
   - MCQ Options and Answers: Storing `[{"key": "A", "text": "2x + 5"}, ...]` inside `questions.options` avoids creating an `options` table with millions of trivial rows.
   - Student Homework Files: Storing `file_s3_keys: ["key1.jpg", "key2.jpg"]` allows multi-page submissions without a dedicated junction table.

4. **Composite Indexes for 150-Student Concurrency**:
   Every query executed on the teacher's dashboard (e.g., "Find all students who have not submitted HW 12", "Find all students who watched Lecture 05") is backed by composite B-tree indexes, ensuring query response times remain under 10ms.
