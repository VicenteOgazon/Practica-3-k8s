USE registro_usuarios;

CREATE TABLE usuarios (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(100),
  apellido VARCHAR(100),
  edad INT,
  correo VARCHAR(150),
  ciudad VARCHAR(100)
);

INSERT INTO usuarios (nombre, apellido, edad, correo, ciudad) VALUES
('Joaquin', 'Paredes', 38, 'joaquin.paredes@example.com', 'Valencia'),
('Elena', 'Santos', 24, 'elena.santos@example.com', 'Madrid'),
('Raul', 'Rivas', 36, 'raul.rivas@example.com', 'Sevilla'),
('Daniela', 'Hernandez', 29, 'daniela.hernandez@example.com', 'Alicante'),
('Martin', 'Vega', 27, 'martin.vega@example.com', 'Bilbao'),
('Carla', 'Jimeno', 31, 'carla.jimeno@example.com', 'Zaragoza'),
('Alex', 'Ramos', 34, 'alex.ramos@example.com', 'Madrid'),
('Marina', 'Ruiz', 25, 'marina.ruiz@example.com', 'Valencia'),
('Oscar', 'Leon', 39, 'oscar.leon@example.com', 'Sevilla'),
('Cristina', 'Ponce', 30, 'cristina.ponce@example.com', 'Murcia'),
('Hector', 'Santos', 28, 'hector.santos@example.com', 'Alicante');