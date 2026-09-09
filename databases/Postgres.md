## DDL

#### CREATE

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE,
    age INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### ALTER

```sql
ALTER TABLE users
ALTER COLUMN name TYPE VARCHAR(50),
ALTER COLUMN name SET NOT NULL;

ALTER TABLE users
DROP COLUMN email;
```

#### DROP

```sql
DROP TABLE users;
```

#### TRUNCATE

```sql
TRUNCATE TABLE users;
```
