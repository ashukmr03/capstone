-- Report A: INNER JOIN of employees and tickets on raised_by, grouped by employee.
-- Returns 11 rows; employees who have never raised a ticket (such as Priya Das, emp_id = 12) are excluded.

SELECT 
    e.emp_id, 
    e.name, 
    e.department, 
    COUNT(t.ticket_id) AS ticket_count
FROM employees e
INNER JOIN tickets t ON e.emp_id = t.raised_by
GROUP BY e.emp_id, e.name, e.department
ORDER BY e.emp_id;
