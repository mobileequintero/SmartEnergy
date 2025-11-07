CREATE DEFINER=`admin`@`%` PROCEDURE `sp_generate_airbnb_devices`()
BEGIN
    DECLARE v_house INT DEFAULT 1;
    DECLARE v_device INT;
    DECLARE v_floor INT;

    -- IDs numéricos
    DECLARE v_devtype_id INT;
    DECLARE v_site_id INT;
    DECLARE v_area_id INT;
    DECLARE v_outlet_id INT;

    -- Atributos textuales
    DECLARE v_hostname VARCHAR(128);
    DECLARE v_ip VARCHAR(45);
    DECLARE v_mac VARCHAR(32);
    DECLARE v_vendor VARCHAR(64);
    DECLARE v_model VARCHAR(64);

    -- Recorre 10 casas (sites)
    WHILE v_house <= 10 DO
        SET v_device = 1;
        SET v_site_id = v_house;              -- site INT (id de casa)

        -- 30 dispositivos por casa
        WHILE v_device <= 30 DO
            SET v_floor   = ((v_device - 1) MOD 3) + 1;   -- 1..3
            SET v_area_id = v_floor;                      -- area INT (id de piso)

            -- Identidad “humana” del equipo (solo para hostname/series)
            SET v_hostname  = CONCAT('device-H', v_house, '_D', v_device);

            -- Datos de red sintéticos
            SET v_ip  = CONCAT('10.', v_house, '.', FLOOR((v_device-1)/254)+1, '.', ((v_device-1) MOD 254)+1);
            SET v_mac = CONCAT('AA:BB:CC:',
                               LPAD(HEX(v_house),2,'0'), ':',
                               LPAD(HEX(v_device DIV 16),2,'0'), ':',
                               LPAD(HEX(v_device MOD 16),2,'0'));

            -- Tipo de dispositivo → ID entero
            CASE (v_device MOD 4)
                WHEN 0 THEN SET v_vendor='Cisco',    v_model='C9300', v_devtype_id=1; -- switch
                WHEN 1 THEN SET v_vendor='Cisco',    v_model='ISR4K', v_devtype_id=2; -- router
                WHEN 2 THEN SET v_vendor='Ubiquiti', v_model='UAP-AC', v_devtype_id=3; -- ap
                ELSE        SET v_vendor='Dell',     v_model='R740',  v_devtype_id=4; -- server
            END CASE;

            -- Tomar un outlet INT al azar
            SELECT outlet_id
              INTO v_outlet_id
              FROM Smart.outlet_specs
              ORDER BY RAND()
              LIMIT 1;

            -- Insertar en inventario: device_id = NULL para usar AUTO_INCREMENT
            CALL Smart.sp_add_network_inventory(
                NULL,                     -- p_device_id INT → AUTO_INCREMENT
                v_hostname,               -- hostname
                v_vendor,                 -- vendor
                v_model,                  -- model
                v_devtype_id,             -- device_type INT
                v_site_id,                -- site INT
                v_area_id,                -- area INT
                v_ip,                     -- mgmt_ip
                v_mac,                    -- mac_address
                'IOS-XE 17.3.1',          -- os_version
                CONCAT('SN', v_house, LPAD(v_device,3,'0')), -- serial_number
                NOW(),                    -- installed_at
                'active',                 -- status (ENUM)
                CONCAT('Synthetic device for Airbnb house ', v_house), -- notes
                v_outlet_id               -- outlet_id INT
            );

            SET v_device = v_device + 1;
        END WHILE;

        SET v_house = v_house + 1;
    END WHILE;
END