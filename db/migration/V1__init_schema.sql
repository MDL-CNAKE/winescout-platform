CREATE TABLE wines (
    id INT AUTO_INCREMENT PRIMARY KEY,
    type ENUM('red','white') NOT NULL,
    fixed_acidity DECIMAL(5,2),
    volatile_acidity DECIMAL(5,3),
    citric_acid DECIMAL(5,2),
    residual_sugar DECIMAL(6,2),
    chlorides DECIMAL(6,3),
    free_sulfur_dioxide DECIMAL(6,1),
    total_sulfur_dioxide DECIMAL(6,1),
    density DECIMAL(9,6),
    ph DECIMAL(4,2),
    sulphates DECIMAL(5,2),
    alcohol DECIMAL(5,2),
    quality TINYINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE quality_predictions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    wine_id INT NOT NULL,
    predicted_quality DECIMAL(4,2) NOT NULL,
    model_version VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (wine_id) REFERENCES wines(id)
);

CREATE TABLE recommendations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    source_wine_id INT NOT NULL,
    recommended_wine_id INT NOT NULL,
    similarity DECIMAL(6,5) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_wine_id) REFERENCES wines(id),
    FOREIGN KEY (recommended_wine_id) REFERENCES wines(id)
);
