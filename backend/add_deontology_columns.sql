-- Ajouter les colonnes d'analyse déontologique à la table articles
ALTER TABLE articles 
ADD COLUMN IF NOT EXISTS score_deontologique NUMERIC,
ADD COLUMN IF NOT EXISTS analyse_deontologique TEXT,
ADD COLUMN IF NOT EXISTS analyzed_at TIMESTAMP WITH TIME ZONE;

-- Créer un index pour améliorer les performances des requêtes sur le score
CREATE INDEX IF NOT EXISTS idx_articles_score_deontologique ON articles(score_deontologique);

-- Commenter les colonnes
COMMENT ON COLUMN articles.score_deontologique IS 'Score déontologique de l''article (0-10)';
COMMENT ON COLUMN articles.analyse_deontologique IS 'Interprétation textuelle de l''analyse déontologique';
COMMENT ON COLUMN articles.analyzed_at IS 'Date de la dernière analyse déontologique';
