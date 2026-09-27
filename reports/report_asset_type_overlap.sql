-- Report E: Set operations on assets linked to ticket types.
-- (i) UNION of assets with incident tickets and assets with maintenance tickets.
-- Returns 8 distinct asset IDs: {1, 2, 3, 4, 5, 6, 8, 11}.

SELECT asset_id 
FROM tickets 
WHERE ticket_type = 'incident' AND asset_id IS NOT NULL
UNION
SELECT asset_id 
FROM tickets 
WHERE ticket_type = 'maintenance' AND asset_id IS NOT NULL
ORDER BY asset_id;

-- (ii) EXCEPT (incident minus maintenance).
-- Returns 4 distinct asset IDs: {3, 4, 8, 11}.

SELECT asset_id 
FROM tickets 
WHERE ticket_type = 'incident' AND asset_id IS NOT NULL
EXCEPT
SELECT asset_id 
FROM tickets 
WHERE ticket_type = 'maintenance' AND asset_id IS NOT NULL
ORDER BY asset_id;
