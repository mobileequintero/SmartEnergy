CREATE DEFINER=`admin`@`%` PROCEDURE `sp_add_raw_temperature`(
    IN p_device_id INT,
    IN p_ts DATE,
    IN p_temp_c_avg DOUBLE,
    IN p_temp_c_min DOUBLE,
    IN p_temp_c_max DOUBLE
)
BEGIN
	INSERT INTO raw_temperature (
        device_id, ts, temp_c_avg, temp_c_min, temp_c_max
    ) VALUES (
        p_device_id, p_ts, p_temp_c_avg, p_temp_c_min, p_temp_c_max
    );
END