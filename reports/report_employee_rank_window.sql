-- Report G: Window function report using RANK() OVER (ORDER BY ticket_count DESC) per raiser.
-- Returns 11 raisers. Aarav Sharma and Arjun Reddy (7 tickets) tie at rank 1.
-- Vivaan Rao (4 tickets) is rank 3 (RANK() skips rank 2 due to tie).

WITH employee_counts AS (
    SELECT 
        e.emp_id, 
        e.name, 
        COUNT(t.ticket_id) AS ticket_count
    FROM employees e
    INNER JOIN tickets t ON e.emp_id = t.raised_by
    GROUP BY e.emp_id, e.name
)
SELECT 
    emp_id, 
    name, 
    ticket_count, 
    RANK() OVER (ORDER BY ticket_count DESC) AS rank
FROM employee_counts
ORDER BY rank, emp_id;
