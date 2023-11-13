-- phpMyAdmin SQL Dump
-- version 5.2.0
-- https://www.phpmyadmin.net/
--
-- Servidor: 127.0.0.1
-- Tiempo de generación: 13-11-2023 a las 19:13:49
-- Versión del servidor: 10.4.27-MariaDB
-- Versión de PHP: 8.2.0

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de datos: `sistema`
--

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `clientes_proveedores`
--

CREATE TABLE `clientes_proveedores` (
  `id` int(10) NOT NULL,
  `nombre` varchar(255) NOT NULL,
  `dni` int(8) NOT NULL,
  `cuit` bigint(11) NOT NULL,
  `numero` varchar(22) NOT NULL,
  `direccion` varchar(255) NOT NULL,
  `saldo` int(11) NOT NULL,
  `tipo` int(5) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `clientes_proveedores`
--

INSERT INTO `clientes_proveedores` (`id`, `nombre`, `dni`, `cuit`, `numero`, `direccion`, `saldo`, `tipo`) VALUES
(1, 'Cliente Generico', 10000000, 0, '2396000000', 'Sin especificar', 0, 1),
(2, 'Proveedor Generico', 0, 10000000000, '2396000000', 'Sin especificar', 0, 2);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `detalles_compra`
--

CREATE TABLE `detalles_compra` (
  `id` int(11) NOT NULL,
  `productos` longtext NOT NULL,
  `total` int(11) NOT NULL,
  `pago` int(11) NOT NULL,
  `diferencia_cliente` int(11) NOT NULL,
  `id_cliente` int(11) NOT NULL,
  `tipo` int(11) NOT NULL,
  `fecha` datetime NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `productos`
--

CREATE TABLE `productos` (
  `id` int(10) NOT NULL,
  `nombre` varchar(255) NOT NULL,
  `tipo` varchar(255) NOT NULL,
  `descripcion` varchar(255) NOT NULL,
  `cantidad` int(11) NOT NULL,
  `precio` int(11) NOT NULL,
  `marca` varchar(255) NOT NULL,
  `minimo` int(11) NOT NULL,
  `salida` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Índices para tablas volcadas
--

--
-- Indices de la tabla `clientes_proveedores`
--
ALTER TABLE `clientes_proveedores`
  ADD PRIMARY KEY (`id`);

--
-- Indices de la tabla `detalles_compra`
--
ALTER TABLE `detalles_compra`
  ADD PRIMARY KEY (`id`);

--
-- Indices de la tabla `productos`
--
ALTER TABLE `productos`
  ADD PRIMARY KEY (`id`);

--
-- AUTO_INCREMENT de las tablas volcadas
--

--
-- AUTO_INCREMENT de la tabla `clientes_proveedores`
--
ALTER TABLE `clientes_proveedores`
  MODIFY `id` int(10) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT de la tabla `detalles_compra`
--
ALTER TABLE `detalles_compra`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `productos`
--
ALTER TABLE `productos`
  MODIFY `id` int(10) NOT NULL AUTO_INCREMENT;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
