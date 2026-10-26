-- SQLite examples for reviewing task data quality and workload.
-- Run these against task_manager.db after creating a few users and tasks.

-- 1. Task counts by status (useful for a small status dashboard).
SELECT status, COUNT(*) AS task_count
FROM tasks
GROUP BY status
ORDER BY status;

-- 2. Task counts by owner, including users with no tasks.
SELECT users.id, users.email, COUNT(tasks.id) AS task_count
FROM users
LEFT JOIN tasks ON tasks.owner_id = users.id
GROUP BY users.id, users.email
ORDER BY task_count DESC, users.id;

-- 3. Data-quality check: find tasks whose status is outside the accepted set.
SELECT id, title, status, owner_id
FROM tasks
WHERE status NOT IN ('todo', 'in_progress', 'done');

-- 4. Data-quality check: find titles that are empty or whitespace-only.
SELECT id, title, owner_id
FROM tasks
WHERE title IS NULL OR LENGTH(TRIM(title)) = 0;
