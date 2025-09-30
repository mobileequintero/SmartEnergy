CREATE DEFINER=`admin`@`%` PROCEDURE `sp_add_raw_lux`(
    IN p_device_id INT,
    IN p_ts TIMESTAMP,
    IN p_illuminance_lux DOUBLE
)
BEGIN
	INSERT INTO raw_lux (
        device_id, ts, illuminance_lux
    ) VALUES (
        p_device_id, p_ts, p_illuminance_lux
    );
    commit;
END