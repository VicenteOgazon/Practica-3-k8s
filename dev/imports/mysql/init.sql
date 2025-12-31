USE registro_usuarios_dev;

CREATE TABLE usuarios (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(100),
  apellido VARCHAR(100),
  edad INT,
  correo VARCHAR(150),
  ciudad VARCHAR(100)
);

INSERT INTO usuarios (nombre, apellido, edad, correo, ciudad) VALUES
('Alejandro', 'Gomez', 29, 'alejandro.gomez@example.com', 'Madrid'),
('Lucia', 'Perez', 34, 'lucia.perez@example.com', 'Barcelona'),
('Carlos', 'Martinez', 41, 'carlos.martinez@example.com', 'Sevilla'),
('Maria', 'Rodriguez', 27, 'maria.rodriguez@example.com', 'Valencia'),
('Javier', 'Lopez', 36, 'javier.lopez@example.com', 'Bilbao'),
('Laura', 'Sanchez', 25, 'laura.sanchez@example.com', 'Granada'),
('Diego', 'Torres', 39, 'diego.torres@example.com', 'Alicante'),
('Ana', 'Diaz', 31, 'ana.diaz@example.com', 'Murcia'),
('Pablo', 'Garcia', 45, 'pablo.garcia@example.com', 'Madrid'),
('Clara', 'Navarro', 28, 'clara.navarro@example.com', 'Málaga'),
('Raul', 'Vega', 42, 'raul.vega@example.com', 'Toledo'),
('Sara', 'Molina', 33, 'sara.molina@example.com', 'Zaragoza');