CREATE DEFINER=`admin`@`%` PROCEDURE `sp_add_network_inventory`(
    IN p_device_id     INT,             -- cambiado de VARCHAR(64) a INT
    IN p_hostname      VARCHAR(128),
    IN p_vendor        VARCHAR(64),
    IN p_model         VARCHAR(64),
    IN p_device_type   INT,             -- cambiado de VARCHAR(16) a INT
    IN p_site          INT,             -- cambiado de VARCHAR(64) a INT
    IN p_area          INT,             -- cambiado de VARCHAR(64) a INT
    IN p_mgmt_ip       VARCHAR(45),
    IN p_mac_address   VARCHAR(32),
    IN p_os_version    VARCHAR(64),
    IN p_serial_number VARCHAR(64),
    IN p_installed_at  DATETIME,
    IN p_status        VARCHAR(16),     -- active / maintenance / retired
    IN p_notes         TEXT,
    IN p_outlet_id     INT              -- cambiado de VARCHAR(64) a INT
)
BEGIN
    INSERT INTO Smart.network_inventory (
        device_id,
        hostname,
        vendor,
        model,
        device_type,
        site,
        area,
        mgmt_ip,
        mac_address,
        os_version,
        serial_number,
        installed_at,
        status,
        notes,
        outlet_id
    ) VALUES (
        p_device_id,
        p_hostname,
        p_vendor,
        p_model,
        p_device_type,
        p_site,
        p_area,
        p_mgmt_ip,
        p_mac_address,
        p_os_version,
        p_serial_number,
        p_installed_at,
        p_status,
        p_notes,
        p_outlet_id
    );
END;
