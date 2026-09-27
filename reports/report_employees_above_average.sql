-- Report D: Scalar subquery listing employees whose ticket count exceeds the average ticket count per raiser.
-- The average across 11 ticket raisers is 30 / 11 ≈ 2.72727.
-- Returns 4 employees: Aarav Sharma (7), Arjun Reddy (7), Vivaan Rao (4), Aditya Menon (3).

SELECT 
    e.emp_id, 
    e.name, 
    COUNT(t.ticket_id) AS ticket_count
FROM employees e
INNER JOIN tickets t ON e.emp_id = t.raised_by
GROUP BY e.emp_id, e.name
HAVING COUNT(t.ticket_id) > (
    SELECT COUNT(*) * 1.0 / COUNT(DISTINCT raised_by) 
    FROM tickets
)
ORDER BY ticket_count DESC, e.emp_id;
