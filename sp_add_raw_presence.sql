CREATE DEFINER=`admin`@`%` PROCEDURE `sp_add_raw_presence`(
    IN p_device_id INT,
    IN p_ts TIMESTAMP,
    IN p_presence TINYINT(1),
    IN p_confidence DOUBLE
)
BEGIN
	INSERT INTO raw_presence (
        device_id, ts, presence, confidence
    ) VALUES (
        p_device_id, p_ts, p_presence, p_confidence
    );
END