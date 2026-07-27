BEGIN TRANSACTION;

INSERT OR IGNORE INTO siro48_table_config
  (id, table_name, table_type, table_path, fields_config, description, create_time, update_time)
VALUES
  ('ae8471ca-40cb-46ba-af9d-574f801add72',
   'GenSIRO48-PTseq-提取产物定量输出表格',
   'Output',
   'D:\data\PTseq_Extraction.xlsx',
   '[{"SampleInfoProperty":"ExtractionQC","ColumnIndex":5}]',
   '建库开始前在POS14 Col7-12完成的提取产物定量结果',
   '2026-07-20 00:00:00',
   '2026-07-20 00:00:00'),
  ('4a42636c-d895-48e2-93e5-40b3415e5ba4',
   'GenSIRO48-PTseq-提取产物均一化输出表格',
   'Output',
   'D:\data\PTseq_normalization_info.csv',
   '[{"SampleInfoProperty":"SampleNumber","ColumnIndex":1},{"SampleInfoProperty":"DnaVolume","ColumnIndex":8},{"SampleInfoProperty":"DnaReplenishmentVolume","ColumnIndex":9}]',
   '20 ng/uL、30 uL目标体系的样本取样量和补水量',
   '2026-07-20 00:00:00',
   '2026-07-20 00:00:00');

-- Library-only: input -> extraction quant -> normalization -> library quant.
INSERT OR IGNORE INTO siro48_script_table_mapping
  (id, script_info_id, table_config_id, order_index)
VALUES
  ('064a4bf8-a150-48bd-8ae7-3b3a0225112e', '47f2bf6c-a6d3-405e-a3a9-65ab8ae84f2d', 'ae8471ca-40cb-46ba-af9d-574f801add72', 2),
  ('0d83707a-8601-4a81-bc1e-c73b85f8a808', '47f2bf6c-a6d3-405e-a3a9-65ab8ae84f2d', '4a42636c-d895-48e2-93e5-40b3415e5ba4', 3);

UPDATE siro48_script_table_mapping
SET order_index = 4
WHERE script_info_id = '47f2bf6c-a6d3-405e-a3a9-65ab8ae84f2d'
AND table_config_id = '376c5abf-c5f3-4781-a6a7-268659a482b9';

-- Full G99/E25/2000&200: add the common PTseq input and both normalization outputs.
INSERT OR IGNORE INTO siro48_script_table_mapping
  (id, script_info_id, table_config_id, order_index)
VALUES
  ('71f7729d-5471-4618-ad44-9bcbb5243502', '69e1bcd1-fe87-4b40-a9d4-93637cedfc39', '26d160f5-8e4f-440c-80f1-6d1248962c80', 1),
  ('f9806fca-58c1-46e4-86ed-ff0cedde1151', 'a09f6afe-95f3-427c-8d7d-e644f2e4ce83', '26d160f5-8e4f-440c-80f1-6d1248962c80', 1),
  ('f66bcdb8-f402-432e-948d-edcd55b46a59', 'aee82507-2a98-41de-a5be-823577f065ac', '26d160f5-8e4f-440c-80f1-6d1248962c80', 1),
  ('e7cf8ede-57c0-4e16-8e1e-0bf18712daa5', '69e1bcd1-fe87-4b40-a9d4-93637cedfc39', 'ae8471ca-40cb-46ba-af9d-574f801add72', 2),
  ('bab14999-1912-4008-a721-bd444e9e3db3', 'a09f6afe-95f3-427c-8d7d-e644f2e4ce83', 'ae8471ca-40cb-46ba-af9d-574f801add72', 2),
  ('5b3acf6d-f79a-4c08-9e00-e4fff4881e08', 'aee82507-2a98-41de-a5be-823577f065ac', 'ae8471ca-40cb-46ba-af9d-574f801add72', 2),
  ('3592f744-5073-4893-a37f-e3807a914514', '69e1bcd1-fe87-4b40-a9d4-93637cedfc39', '4a42636c-d895-48e2-93e5-40b3415e5ba4', 3),
  ('19a0ae77-555d-4238-b83e-e097df266b08', 'a09f6afe-95f3-427c-8d7d-e644f2e4ce83', '4a42636c-d895-48e2-93e5-40b3415e5ba4', 3),
  ('b3b04173-152a-4c4a-88c0-89ddd270642c', 'aee82507-2a98-41de-a5be-823577f065ac', '4a42636c-d895-48e2-93e5-40b3415e5ba4', 3);

UPDATE siro48_script_table_mapping
SET order_index = 4
WHERE script_info_id IN (
  '69e1bcd1-fe87-4b40-a9d4-93637cedfc39',
  'a09f6afe-95f3-427c-8d7d-e644f2e4ce83',
  'aee82507-2a98-41de-a5be-823577f065ac'
)
AND table_config_id = '376c5abf-c5f3-4781-a6a7-268659a482b9';

UPDATE siro48_script_table_mapping
SET order_index = 5
WHERE script_info_id IN (
  '69e1bcd1-fe87-4b40-a9d4-93637cedfc39',
  'a09f6afe-95f3-427c-8d7d-e644f2e4ce83',
  'aee82507-2a98-41de-a5be-823577f065ac'
)
AND table_config_id = '13f49971-63b2-4b98-98af-9b452325c280';

COMMIT;
