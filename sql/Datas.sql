INSERT INTO role (name) VALUES
('Commercial'),
('Gestionnaire de stock'),
('Administrateur');

INSERT INTO category (name) VALUES
('Portes intérieures'),
('Panneaux sandwich'),
('Peinture'),
('Électricité'),
('Quincaillerie');

INSERT INTO unit (name) VALUES
('pce'),
('m²'),
('fût'),
('pot'),
('m');

INSERT INTO product (designation, purchase_unit_price, sale_unit_price, coefficient, unit_id, category_id) VALUES
('Porte battante XL - Finition Chêne', 450, 585, 1, 1, 1),
('Porte battante XL - Finition Blanc', 420, 546, 1, 1, 1),
('Porte coulissante - Finition Chêne', 680, 884, 1, 1, 1),
('Porte coulissante - Finition Blanc', 620, 806, 1, 1, 1),
('Panneau cloisonnage 4cm - Blanc', 85, 110.5, 1, 2, 2),
('Panneau cloisonnage 6cm - Blanc', 105, 136.5, 1, 2, 2),
('Panneau cloisonnage 4cm - Gris', 90, 117, 1, 2, 2),
('Peinture murs - Gris clair (200L)', 180, 234, 1, 3, 3),
('Peinture murs - Blanc pur (200L)', 165, 214.5, 1, 3, 3),
('Peinture trim - Gris anthracite (5L)', 45, 58.5, 1, 4, 3),
('Goulotte électrique 40x40', 12, 15.6, 1, 5, 4),
('Prise double - Blanc', 22, 28.6, 1, 1, 4),
('Interrupteur simple - Blanc', 18, 23.4, 1, 1, 4),
('Poignée chrome XXL', 35, 45.5, 1, 1, 5),
('Charnière acier inox', 8, 10.4, 1, 1, 5);

INSERT INTO company_type (name) VALUES
('SARL'),
('SAS'),
('SA'),
('EURL'),
('Auto-entrepreneur');

INSERT INTO client (name, address, email, website_url, phone, is_company) VALUES
('Jean Dupont', '12 Rue de la Paix, 75002 Paris', 'contact@dupont-entreprise.fr', 'https://www.dupont-entreprise.fr', '+33 1 42 61 12 34', FALSE),
('Marie Martin', '25 Avenue Victor Hugo, 75116 Paris', 'bonjour@martin-design.com', 'https://www.martin-design.com', '+33 1 45 00 23 45', FALSE),
('Pierre Bernard', '8 Place Bellecour, 69002 Lyon', 'info@bernard-conseil.fr', 'https://www.bernard-conseil.fr', '+33 4 78 37 45 67', FALSE),
('Sophie Petit', '35 Rue Saint-Ferréol, 13001 Marseille', 'contact@petit-import.com', 'https://www.petit-import.com', '+33 4 91 54 67 89', FALSE),
('Thomas Robert', '42 Rue Nationale, 59000 Lille', 'hello@robert-tech.fr', 'https://www.robert-tech.fr', '+33 3 20 15 78 90', FALSE),
('SARL Richard & Fils', '5 Rue de la République, 69001 Lyon', 'contact@richard-sante.fr', 'https://www.richard-sante.fr', '+33 4 72 10 34_56', TRUE),
('SAS Simon Distribution', '18 Rue du Faubourg Saint-Honoré, 75008 Paris', 'info@simon-luxe.com', 'https://www.simon-luxe.com', '+33 1 53 43 67 89', TRUE),
('SA Michel Aérospatiale', '3 Place du Capitole, 31000 Toulouse', 'contact@michel-aero.fr', 'https://www.michel-aero.fr', '+33 5 61 23 45 67', TRUE),
('EURL Laurent Vignobles', '27 Rue de la Liberté, 21000 Dijon', 'bonjour@laurent-vins.fr', 'https://www.laurent-vins.fr', '+33 3 80 30 67 89', TRUE),
('Dubois Technologies', '15 Quai des Belges, 34000 Montpellier', 'contact@dubois-tech.com', 'https://www.dubois-tech.com', '+33 4 67 12 34 56', TRUE);

INSERT INTO individual (first_name, last_name, birth_date, id_card_number, client_id) VALUES
('Jean', 'Dupont', '1975-03-15', 'CNI123456789', 1),
('Marie', 'Martin', '1982-07-22', 'CNI987654321', 2),
('Pierre', 'Bernard', '1968-11-30', 'CNI456789123', 3),
('Sophie', 'Petit', '1990-05-18', 'CNI789123456', 4),
('Thomas', 'Robert', '1985-09-08', 'CNI321654987', 5);

INSERT INTO company (name, registration_number, tax_identification_number, created_at, company_type_id, client_id) VALUES
('SARL Richard & Fils', 'RCS LYON 123 456 789', 'TVA FR12345678901', '2018-04-12', 1, 6),
('SAS Simon Distribution', 'RCS PARIS 987 654 321', 'TVA FR98765432109', '2015-09-23', 2, 7),
('SA Michel Aérospatiale', 'RCS TOULOUSE 456 789 123', 'TVA FR45678912345', '2010-02-01', 3, 8),
('EURL Laurent Vignobles', 'RCS DIJON 789 123 456', 'TVA FR78912345678', '2019-11-15', 4, 9),
('Dubois Technologies', 'RCS MONTPELLIER 321 654 987', 'TVA FR32165498701', '2020-06-30', 5, 10);