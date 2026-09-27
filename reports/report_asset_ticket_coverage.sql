-- Report C: LEFT JOIN of assets and tickets on asset_id, counting tickets per asset with COUNT(t.ticket_id).
-- Query 1: Asset ticket coverage for all assets (AST-018 has ticket count 0).

SELECT 
    a.asset_id, 
    a.asset_tag, 
    a.category, 
    COUNT(t.ticket_id) AS ticket_count
FROM assets a
LEFT JOIN tickets t ON a.asset_id = t.asset_id
GROUP BY a.asset_id, a.asset_tag, a.category
ORDER BY a.asset_id;

-- Query 2: Independent confirmation of assets with zero tickets using NOT IN subquery.
SELECT 
    asset_id, 
    asset_tag, 
    category
FROM assets
WHERE asset_id NOT IN (
    SELECT DISTINCT asset_id 
    FROM tickets 
    WHERE asset_id IS NOT NULL
)
ORDER BY asset_id;
