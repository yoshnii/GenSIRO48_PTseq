PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "worklistrule" (
  "id" text NOT NULL,
  "name" TEXT,
  "value" TEXT,
  "param_count" TEXT,
  "example" TEXT,
  "explain" TEXT,
  "remark" TEXT,
  PRIMARY KEY ("id")
);
INSERT INTO worklistrule VALUES('1','固定值','fix_value','1','{fix_value: {value}}','参数值填50,移液表格的值也是50','已实现');
INSERT INTO worklistrule VALUES('2','SIRO样本信息字段','SIRO16_sample_property','1','{SIRO16_sample_property: {sample_property}}','参数值填孔位，移液表格的值取样本信息的孔位那列的值','已实现');
INSERT INTO worklistrule VALUES('3','根据样本信息字段在扫码结果中寻板位','scan_result_position','1','{scan_result_position: {sample_property} }','从扫码结果寻找等于样本信息中参数1那列值的Position','已实现');
INSERT INTO worklistrule VALUES('4','根据样本信息字段在扫码结果中寻耗材','scan_result_consumable','1','{scan_result_consumable: {sample_property} }','从扫码结果寻找等于样本信息中参数1那列值的Consumable','已实现');
INSERT INTO worklistrule VALUES('5','Pooling策略计算孔位','pooling_rule_site','1','{pooling_rule_site: {sample_property}}','Pooling策略计算孔位后取字段值','已实现');
INSERT INTO worklistrule VALUES('6','SIRO样本字段值判断取值','SIRO16_sample_property_value_equal','4','{SIRO16_sample_property_value_equal:{sample_property,equalvalue,value1,value2}}','样本信息的sample_property字段值在参数2的列表内（以,间隔），取param3,否则取param4','已实现');
INSERT INTO worklistrule VALUES('7','序列递增值','increase_sequence','2','{increase_sequence:{value，value2}}','每行的值从参数1开始按参数2等差递增','已实现');
INSERT INTO worklistrule VALUES('8','Pooling策略计算体积','pooling_rule_volumn','1','{pooling_rule_volumn: {sample_property}}','Pooling策略计算体积','已实现');
INSERT INTO worklistrule VALUES('9','列表序列取值','list_sequence_value','1','{list_sequence_value: {value}}','按顺序取参数列表内的值,以英文逗号,间隔取值','已实现');
INSERT INTO worklistrule VALUES('10','在字段值筛选后的序列号','filter_value_sequence','2','{filter_value_sequence: {sample_property,value,value}}','该样本在param1字段属性值为param2（以,间隔）样本列表内的序列号+param3','已实现');
INSERT INTO worklistrule VALUES('11','固定值加SIRO样本信息字段','fix_value_add_SIRO16_sample_property','2','{fix_value_add_SIRO16_sample_property: {sample_property,value}}','该样本参数1字段属性值加参数2','已实现');
INSERT INTO worklistrule VALUES('12','信息字段筛选个数起始递增值','SIRO16_sample_property_value_increase_sequence','4','{SIRO16_sample_property_value_increase_sequence:{sample_property,value1,value2,value3}}','以param3加上在所有样本内param1字段值在param2内的个数后以param4等差递增','已实现');
INSERT INTO worklistrule VALUES('13','样本序号判断取值','order_equal','2','{increase_sequence:{value，value2}}','param1为序号区间（左开右闭），param2为取值，都以,间隔','已实现');
INSERT INTO worklistrule VALUES('14','两次SIRO样本字段值判断取值','twice_value_equal','7','{twice_value_equal:{SAMPLE,VALUE1,VALUE2,SAMPLE2,VALUE3,VALUE4，VALUE5}}','样本信息字段param1取值在param2内取param3,否则param4取值在param5内取param6,否则取param7','已实现');
INSERT INTO worklistrule VALUES('15','样本信息字段排序取列表递增值','sample_property_sort_list_sequence_value','2','{sample_property_sort_list_sequence_value:{SAMPLE,VALUE2}}','以样本param1字段值在样本中的区号再按顺序取param2参数列表内的值,以英文逗号,间隔取值','已实现');
INSERT INTO worklistrule VALUES('16','固定值除以样本信息字段结果加固定值','value_divide_sample_property_add_value','3','{value_divide_add_value: {sample_property,value,value}}','param2除以param1字段值加上param3','已实现');
INSERT INTO worklistrule VALUES('17','固定值减去固定值除以样本信息字段结果','value_sub_value_divide_sample_property','3','{value_sub_value_divide_sample_property: {sample_property,value,value}}','param3减去param2除以param1字段值','已实现');
CREATE TABLE IF NOT EXISTS "selecttype" (
  "judge_type" TEXT,
  "name" TEXT
);
INSERT INTO selecttype VALUES('去重','去重');
INSERT INTO selecttype VALUES('等于','等于');
INSERT INTO selecttype VALUES('not in list','不在列表内');
INSERT INTO selecttype VALUES('more than','大于等于');
INSERT INTO selecttype VALUES('less than','小于');
CREATE TABLE IF NOT EXISTS "equipment_type" (
  "id" INTEGER NOT NULL,
  "equipment_id" text,
  "equipment_name" TEXT,
  "is_scan" TEXT,
  "is_execute_script" TEXT,
  "is_show_image" TEXT,
  "is_update_data" TEXT,
  "remark" TEXT,
  PRIMARY KEY ("id")
);
INSERT INTO equipment_type VALUES(1,'equipment0000001','建库仪','0','1','0','0',NULL);
INSERT INTO equipment_type VALUES(2,'equipment0000002','前处理仪','1','1','0','0',NULL);
INSERT INTO equipment_type VALUES(3,'equipment0000003','手动扫码枪','1','0','0','0',NULL);
INSERT INTO equipment_type VALUES(4,'equipment0000004','图片弹窗','0','0','1','0',NULL);
INSERT INTO equipment_type VALUES(5,'equipment0000005','Barcode录入','0','0','0','1',NULL);
INSERT INTO equipment_type VALUES(6,'equipment0000006','48提取','1','1','0','0',NULL);
INSERT INTO equipment_type VALUES(8,'equipment0000007','48建库','1','1','0','0',NULL);
CREATE TABLE IF NOT EXISTS "script_worklist" (
  "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
  "order_index" integer,
  "script_id" text NOT NULL,
  "script_name" TEXT,
  "worklist_id" text NOT NULL,
  "worklist_name" TEXT
);
INSERT INTO script_worklist VALUES(149,1,'c37cd8c0-45da-4206-bfb6-b1280a066b51','NIFTY48提取','1bf2a5e4-7482-477a-9872-a676d9e3286b','NIFTY提取');
INSERT INTO script_worklist VALUES(155,1,'367507f9-fc75-49f5-b0be-42224ef963bf','康孕提取_测试','064b5631-f318-425a-8f14-caa734537b3d','CNVSeq48');
INSERT INTO script_worklist VALUES(160,1,'d007de0c-c944-49f5-bcb2-4124bd0eb002','CNVSeq48提取','064b5631-f318-425a-8f14-caa734537b3d','CNVSeq48');
INSERT INTO script_worklist VALUES(161,1,'9c0441b6-a399-495f-a8f6-41768588192a','Siro48-NIFTY-提取-V1.8','a968d490-5242-407a-b69e-41d5a7136ca7','NIFTY48');
CREATE TABLE IF NOT EXISTS "process_type" (
  "process_type_name" TEXT,
  "process_type_value" TEXT
);
INSERT INTO process_type VALUES('样本前处理','PreTreatment');
INSERT INTO process_type VALUES('建库','LibraryPrep');
INSERT INTO process_type VALUES('杂洗','Hybridization');
INSERT INTO process_type VALUES('上机前准备','SequencingPrep');
INSERT INTO process_type VALUES('过夜孵育','SaveProduct');
CREATE TABLE IF NOT EXISTS "equipment" (
  "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
  "equipment_code" TEXT,
  "equipment_name" TEXT,
  "equipment_id" text,
  "remark" TEXT
);
INSERT INTO equipment VALUES(1,'code0000001','建库仪','equipment0000001',NULL);
INSERT INTO equipment VALUES(2,'code0000002','前处理仪','equipment0000002',NULL);
INSERT INTO equipment VALUES(3,'code0000003','手动扫码枪','equipment0000003',NULL);
INSERT INTO equipment VALUES(4,'code0000004','图片弹窗','equipment0000004',NULL);
INSERT INTO equipment VALUES(5,'code0000005','Barcode录入','equipment0000005',NULL);
INSERT INTO equipment VALUES(6,'code0000006','48提取','equipment0000006',NULL);
INSERT INTO equipment VALUES(7,'code0000007','48建库','equipment0000007',NULL);
CREATE TABLE IF NOT EXISTS "workflow" (
  "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
  "order_index" TEXT,
  "process_id" text,
  "process_name" TEXT,
  "equipment_code" TEXT,
  "equipment_name" TEXT,
  "method" TEXT,
  "param_string" TEXT,
  "remark" TEXT
);
INSERT INTO workflow VALUES(649,'1','f33df7a7-e3b5-4830-bf74-3db4a911145a','GenSIRO48-PTseq-提取（全流程）','code0000007','48建库','ExecuteExperiment','{"ScriptId": "cc5f0fa6-81fa-427f-a754-48a587116279", "ScriptName": "SIRO48-PTseq-开启温控", "MethodType": "ExecuteExperiment", "DeskData": "", "PositionParams": "", "PlateTypeAssociation": "Library"}',NULL);
INSERT INTO workflow VALUES(650,'2','f33df7a7-e3b5-4830-bf74-3db4a911145a','GenSIRO48-PTseq-提取（全流程）','code0000004','图片弹窗','ShowPicture','{"Path": "Resources\\PTseq-layout\\SIRO48-PTseq-Full-Process-Extraction.jpg", "Remark": null}',NULL);
INSERT INTO workflow VALUES(651,'3','f33df7a7-e3b5-4830-bf74-3db4a911145a','GenSIRO48-PTseq-提取（全流程）','code0000004','图片弹窗','ShowPicture','{"Path": "Resources\\PTseq-layout\\SIRO48-PTseq-Full-Process-Library.jpg", "Remark": null}',NULL);
INSERT INTO workflow VALUES(652,'4','f33df7a7-e3b5-4830-bf74-3db4a911145a','GenSIRO48-PTseq-提取（全流程）','code0000004','图片弹窗','ShowPicture','{"Path": "Resources\\PTseq-layout\\SIRO48-PTseq-Full-Process Reagent Bench Diagram(G99&200).jpg", "Remark": null}',NULL);
INSERT INTO workflow VALUES(653,'5','f33df7a7-e3b5-4830-bf74-3db4a911145a','GenSIRO48-PTseq-提取（全流程）','code0000006','48提取','DeckScan','{"ScriptId": "", "ScriptName": "", "ScanString": "[{\"lane\": 1, \"pos\": 1, \"consumable\": \"1\", \"barcode\": null, \"position\": \"1\", \"barcode_number_type\": null, \"result\": \"1\", \"error_message\": null, \"is_row_valid\": false, \"IsSelect\": false, \"Sort\": 1, \"OrderIndex\": 1, \"Index\": 1, \"IsLocked\": false, \"ValidationBackgroundColor\": \"Transparent\", \"IsInputReadOnly\": false, \"sample_number\": null, \"IsScan\": false}]", "DeskData": "", "PositionParams": "", "PlateTypeAssociation": "Pretreatment"}',NULL);
INSERT INTO workflow VALUES(654,'6','f33df7a7-e3b5-4830-bf74-3db4a911145a','GenSIRO48-PTseq-提取（全流程）','code0000005','Barcode录入','UpdateBarcodeId','{"SampleInfoProperty": "BarcodeId", "ScanString": "[{\"lane\": 1, \"pos\": 1, \"consumable\": \"1\", \"barcode\": null, \"position\": \"1\", \"barcode_number_type\": null, \"result\": \"1\", \"error_message\": null, \"is_row_valid\": false, \"IsSelect\": false, \"Sort\": 1, \"OrderIndex\": 1, \"Index\": 1, \"sample_number\": null, \"IsScan\": false}]"}',NULL);
INSERT INTO workflow VALUES(655,'7','f33df7a7-e3b5-4830-bf74-3db4a911145a','GenSIRO48-PTseq-提取（全流程）','code0000006','48提取','ExecuteExperiment','{"ScriptId": "2025ec6a-8bac-4349-97bb-a93a6fc7d528", "ScriptName": "GenSIRO48-PTseq-提取", "ScanString": "", "DeskData": "", "PositionParams": "", "PlateTypeAssociation": "Pretreatment"}',NULL);
INSERT INTO workflow VALUES(656,'1','ae66a0e8-32f6-4a3c-98bd-6862d1db80dc','GenSIRO48-PTseq-建库及上机前准备-E25','code0000007','48建库','ExecuteExperiment','{"ScriptId": "a09f6afe-95f3-427c-8d7d-e644f2e4ce83", "ScriptName": "GenSIRO48-PTseq-建库及上机前准备-E25", "MethodType": "ExecuteExperiment", "DeskData": "", "PositionParams": "", "PlateTypeAssociation": "Library"}',NULL);
INSERT INTO workflow VALUES(657,'1','3168b048-41af-4c36-991d-a93838750c0b','GenSIRO48-PTseq-建库及上机前准备-G99','code0000007','48建库','ExecuteExperiment','{"ScriptId": "69e1bcd1-fe87-4b40-a9d4-93637cedfc39", "ScriptName": "GenSIRO48-PTseq-建库及上机前准备-G99", "MethodType": "ExecuteExperiment", "DeskData": "", "PositionParams": "", "PlateTypeAssociation": "Library"}',NULL);
INSERT INTO workflow VALUES(658,'1','d981428e-9a8f-4fff-aebb-841cf48853f2','GenSIRO48-PTseq-建库及上机前准备-200','code0000007','48建库','ExecuteExperiment','{"ScriptId": "aee82507-2a98-41de-a5be-823577f065ac", "ScriptName": "GenSIRO48-PTseq-建库及上机前准备-2000&200", "MethodType": "ExecuteExperiment", "DeskData": "", "PositionParams": "", "PlateTypeAssociation": "Library"}',NULL);
INSERT INTO workflow VALUES(659,'1','da0bbb53-c5d7-4268-8939-69b8f743c921','GenSIRO48-PTseq-fake-上机前准备','code0000007','48建库','ExecuteExperiment','{"ScriptId": "5468c284-39a6-4370-919a-36714e9160bb", "ScriptName": "GenSIRO48-PTseq-fake-上机前准备", "MethodType": "ExecuteExperiment", "DeskData": "", "PositionParams": "", "PlateTypeAssociation": "Library"}',NULL);
INSERT INTO workflow VALUES(660,'1','eab536d5-e9e6-4332-b8a2-35e1718b1a4e','GenSIRO48-PTseq-提取（提取-建库）','code0000007','48建库','ExecuteExperiment','{"ScriptId": "cc5f0fa6-81fa-427f-a754-48a587116279", "ScriptName": "SIRO48-PTseq-开启温控", "MethodType": "ExecuteExperiment", "DeskData": "", "PositionParams": "", "PlateTypeAssociation": "Library"}',NULL);
INSERT INTO workflow VALUES(661,'2','eab536d5-e9e6-4332-b8a2-35e1718b1a4e','GenSIRO48-PTseq-提取（提取-建库）','code0000004','图片弹窗','ShowPicture','{"Path": "Resources\\PTseq-layout\\SIRO48-PTseq-Full-Process-Extraction.jpg", "Remark": null}',NULL);
INSERT INTO workflow VALUES(662,'3','eab536d5-e9e6-4332-b8a2-35e1718b1a4e','GenSIRO48-PTseq-提取（提取-建库）','code0000004','图片弹窗','ShowPicture','{"Path": "Resources\\PTseq-layout\\SIRO48-PTseq-Pretreatment-Library.jpg", "Remark": null}',NULL);
INSERT INTO workflow VALUES(663,'4','eab536d5-e9e6-4332-b8a2-35e1718b1a4e','GenSIRO48-PTseq-提取（提取-建库）','code0000004','图片弹窗','ShowPicture','{"Path": "Resources\\PTseq-layout\\SIRO48-PTseq-Pretreatment-Library Reagent Bench Diagram.jpg", "Remark": null}',NULL);
INSERT INTO workflow VALUES(664,'5','eab536d5-e9e6-4332-b8a2-35e1718b1a4e','GenSIRO48-PTseq-提取（提取-建库）','code0000006','48提取','DeckScan','{"ScriptId": "", "ScriptName": "", "ScanString": "[{\"lane\": 1, \"pos\": 1, \"consumable\": \"1\", \"barcode\": null, \"position\": \"1\", \"barcode_number_type\": null, \"result\": \"1\", \"error_message\": null, \"is_row_valid\": false, \"IsSelect\": false, \"Sort\": 1, \"OrderIndex\": 1, \"Index\": 1, \"IsLocked\": false, \"ValidationBackgroundColor\": \"Transparent\", \"IsInputReadOnly\": false, \"sample_number\": null, \"IsScan\": false}]", "DeskData": "", "PositionParams": "", "PlateTypeAssociation": "Pretreatment"}',NULL);
INSERT INTO workflow VALUES(665,'6','eab536d5-e9e6-4332-b8a2-35e1718b1a4e','GenSIRO48-PTseq-提取（提取-建库）','code0000005','Barcode录入','UpdateBarcodeId','{"SampleInfoProperty": "BarcodeId", "ScanString": "[{\"lane\": 1, \"pos\": 1, \"consumable\": \"1\", \"barcode\": null, \"position\": \"1\", \"barcode_number_type\": null, \"result\": \"1\", \"error_message\": null, \"is_row_valid\": false, \"IsSelect\": false, \"Sort\": 1, \"OrderIndex\": 1, \"Index\": 1, \"sample_number\": null, \"IsScan\": false}]"}',NULL);
INSERT INTO workflow VALUES(666,'7','eab536d5-e9e6-4332-b8a2-35e1718b1a4e','GenSIRO48-PTseq-提取（提取-建库）','code0000006','48提取','ExecuteExperiment','{"ScriptId": "2025ec6a-8bac-4349-97bb-a93a6fc7d528", "ScriptName": "GenSIRO48-PTseq-提取", "ScanString": "", "DeskData": "", "PositionParams": "", "PlateTypeAssociation": "Pretreatment"}',NULL);
INSERT INTO workflow VALUES(667,'1','b11875de-7bf3-43d9-98bd-ed349a9aa2f0','GenSIRO48-PTseq-建库','code0000007','48建库','ExecuteExperiment','{"ScriptId": "47f2bf6c-a6d3-405e-a3a9-65ab8ae84f2d", "ScriptName": "GenSIRO48-PTseq-建库", "MethodType": "ExecuteExperiment", "DeskData": "", "PositionParams": "", "PlateTypeAssociation": "Library"}',NULL);
INSERT INTO workflow VALUES(668,'1','7e95994e-09e2-4f42-8ecd-512d84f3a1c2','GenSIRO48-PTseq-上机前准备-E25','code0000004','Image Popup','ShowPicture','{"Path": "Resources\\PTseq-layout\\SIRO48-PTseq SequencingPrep Bench Diagram.jpg", "Remark": null}',NULL);
INSERT INTO workflow VALUES(669,'2','7e95994e-09e2-4f42-8ecd-512d84f3a1c2','GenSIRO48-PTseq-上机前准备-E25','code0000004','Image Popup','ShowPicture','{"Path": "Resources\\PTseq-layout\\SIRO48-PTseq SequencingPrep Reagent Bench Diagram(E25).jpg", "Remark": null}',NULL);
INSERT INTO workflow VALUES(670,'3','7e95994e-09e2-4f42-8ecd-512d84f3a1c2','GenSIRO48-PTseq-上机前准备-E25','code0000007','48 Library Prep','PlateScan','{"ScriptId": "", "ScriptName": "", "MethodType": "PlateScan", "DeskData": "D:\\SIRO48\\Scripts\\Users\\LibraryBuilding\\GenSIRO48-PTseq-SequencingPrep-E25.zip", "PositionParams": "{\"WorkstationType\": \"LIBRARY\", \"PlateGroups\": [{\"GroupName\": \"\\u7b2c1\\u5757\\u677f\", \"Positions\": [\"M2_POS6\"]}, {\"GroupName\": \"\\u7b2c2\\u5757\\u677f\", \"Positions\": [\"M2_POS7\"]}, {\"GroupName\": \"\\u7b2c3\\u5757\\u677f\", \"Positions\": [\"M2_POS11\"]}, {\"GroupName\": \"\\u7b2c4\\u5757\\u677f\", \"Positions\": [\"M2_POS13\"]}]}", "PlateTypeAssociation": "Library"}',NULL);
INSERT INTO workflow VALUES(671,'4','7e95994e-09e2-4f42-8ecd-512d84f3a1c2','GenSIRO48-PTseq-上机前准备-E25','code0000007','48 Library Prep','ExecuteExperiment','{"ScriptId": "8ec0aa83-2ef6-4706-94a6-3f0aec99dcf9", "ScriptName": "GenSIRO48-PTseq-上机前准备-E25", "MethodType": "ExecuteExperiment", "DeskData": "", "PositionParams": "", "PlateTypeAssociation": "Library"}',NULL);
INSERT INTO workflow VALUES(672,'1','a830c028-f1bd-46cb-8b17-de09138e0eb5','GenSIRO48-PTseq-上机前准备-G99','code0000004','Image Popup','ShowPicture','{"Path": "Resources\\PTseq-layout\\SIRO48-PTseq SequencingPrep Bench Diagram.jpg", "Remark": null}',NULL);
INSERT INTO workflow VALUES(673,'2','a830c028-f1bd-46cb-8b17-de09138e0eb5','GenSIRO48-PTseq-上机前准备-G99','code0000004','Image Popup','ShowPicture','{"Path": "Resources\\PTseq-layout\\SIRO48-PTseq SequencingPrep Reagent Bench Diagram(G99&200).jpg", "Remark": null}',NULL);
INSERT INTO workflow VALUES(674,'3','a830c028-f1bd-46cb-8b17-de09138e0eb5','GenSIRO48-PTseq-上机前准备-G99','code0000007','48 Library Prep','PlateScan','{"ScriptId": "", "ScriptName": "", "MethodType": "PlateScan", "DeskData": "D:\\SIRO48\\Scripts\\Users\\LibraryBuilding\\GenSIRO48-PTseq-SequencingPrep-G99.zip", "PositionParams": "{\"WorkstationType\": \"LIBRARY\", \"PlateGroups\": [{\"GroupName\": \"\\u7b2c1\\u5757\\u677f\", \"Positions\": [\"M2_POS6\"]}, {\"GroupName\": \"\\u7b2c2\\u5757\\u677f\", \"Positions\": [\"M2_POS7\"]}, {\"GroupName\": \"\\u7b2c3\\u5757\\u677f\", \"Positions\": [\"M2_POS11\"]}, {\"GroupName\": \"\\u7b2c4\\u5757\\u677f\", \"Positions\": [\"M2_POS13\"]}]}", "PlateTypeAssociation": "Library"}',NULL);
INSERT INTO workflow VALUES(675,'4','a830c028-f1bd-46cb-8b17-de09138e0eb5','GenSIRO48-PTseq-上机前准备-G99','code0000007','48 Library Prep','ExecuteExperiment','{"ScriptId": "27e2a5bb-3fc7-4565-b807-7ef90200d99b", "ScriptName": "GenSIRO48-PTseq-上机前准备-G99", "MethodType": "ExecuteExperiment", "DeskData": "", "PositionParams": "", "PlateTypeAssociation": "Library"}',NULL);
INSERT INTO workflow VALUES(676,'1','84e67d61-e6cd-401a-bb5a-e3db66181bce','GenSIRO48-PTseq-上机前准备-200','code0000004','Image Popup','ShowPicture','{"Path": "Resources\\PTseq-layout\\SIRO48-PTseq SequencingPrep Bench Diagram.jpg", "Remark": null}',NULL);
INSERT INTO workflow VALUES(677,'2','84e67d61-e6cd-401a-bb5a-e3db66181bce','GenSIRO48-PTseq-上机前准备-200','code0000004','Image Popup','ShowPicture','{"Path": "Resources\\PTseq-layout\\SIRO48-PTseq SequencingPrep Reagent Bench Diagram(G99&200).jpg", "Remark": null}',NULL);
INSERT INTO workflow VALUES(678,'3','84e67d61-e6cd-401a-bb5a-e3db66181bce','GenSIRO48-PTseq-上机前准备-200','code0000007','48 Library Prep','PlateScan','{"ScriptId": "", "ScriptName": "", "MethodType": "PlateScan", "DeskData": "D:\\SIRO48\\Scripts\\Users\\LibraryBuilding\\GenSIRO48-PTseq-SequencingPrep-2000&200.zip", "PositionParams": "{\"WorkstationType\": \"LIBRARY\", \"PlateGroups\": [{\"GroupName\": \"\\u7b2c1\\u5757\\u677f\", \"Positions\": [\"M2_POS6\"]}, {\"GroupName\": \"\\u7b2c2\\u5757\\u677f\", \"Positions\": [\"M2_POS7\"]}, {\"GroupName\": \"\\u7b2c3\\u5757\\u677f\", \"Positions\": [\"M2_POS11\"]}, {\"GroupName\": \"\\u7b2c4\\u5757\\u677f\", \"Positions\": [\"M2_POS13\"]}]}", "PlateTypeAssociation": "Library"}',NULL);
INSERT INTO workflow VALUES(679,'4','84e67d61-e6cd-401a-bb5a-e3db66181bce','GenSIRO48-PTseq-上机前准备-200','code0000007','48 Library Prep','ExecuteExperiment','{"ScriptId": "11547208-aef4-42e6-9061-1d2a9dea720a", "ScriptName": "GenSIRO48-PTseq-上机前准备-200", "MethodType": "ExecuteExperiment", "DeskData": "", "PositionParams": "", "PlateTypeAssociation": "Library"}',NULL);
INSERT INTO workflow VALUES(680,'1','003f01ca-bd44-4142-9a2f-e4ee87cba24b','GenSIRO48-过夜孵育','code0000007','48建库','ExecuteExperiment','{"ScriptId": "ab8eba8f-a258-4b05-9ddb-287678a4adc8", "ScriptName": "GenSIRO48-PTseq-过夜孵育", "MethodType": "ExecuteExperiment", "DeskData": "", "PositionParams": "", "PlateTypeAssociation": "Library"}',NULL);
INSERT INTO workflow VALUES(681,'1','d20649e5-f920-46f8-b2a2-3a58e29bdff0','GenSIRO48-PTseq-DNB孵育','code0000007','48建库','ExecuteExperiment','{"ScriptId": "29051113-3662-43aa-877d-56c750bebee3", "ScriptName": "GenSIRO48-PTseq-DNB孵育", "MethodType": "ExecuteExperiment", "DeskData": "", "PositionParams": "", "PlateTypeAssociation": "Library"}',NULL);
INSERT INTO workflow VALUES(682,'1','fa5f7e77-4005-434b-bafb-2e7f9896ab26','GenSIRO48-PTseq-提取（全流程E25）','code0000007','48建库','ExecuteExperiment','{"ScriptId": "cc5f0fa6-81fa-427f-a754-48a587116279", "ScriptName": "SIRO48-PTseq-开启温控", "MethodType": "ExecuteExperiment", "DeskData": "", "PositionParams": "", "PlateTypeAssociation": "Library"}',NULL);
INSERT INTO workflow VALUES(683,'2','fa5f7e77-4005-434b-bafb-2e7f9896ab26','GenSIRO48-PTseq-提取（全流程E25）','code0000004','图片弹窗','ShowPicture','{"Path": "Resources\\PTseq-layout\\SIRO48-PTseq-Full-Process-Extraction.jpg", "Remark": null}',NULL);
INSERT INTO workflow VALUES(684,'3','fa5f7e77-4005-434b-bafb-2e7f9896ab26','GenSIRO48-PTseq-提取（全流程E25）','code0000004','图片弹窗','ShowPicture','{"Path": "Resources\\PTseq-layout\\SIRO48-PTseq-Full-Process-Library.jpg", "Remark": null}',NULL);
INSERT INTO workflow VALUES(685,'4','fa5f7e77-4005-434b-bafb-2e7f9896ab26','GenSIRO48-PTseq-提取（全流程E25）','code0000004','图片弹窗','ShowPicture','{"Path": "Resources\\PTseq-layout\\SIRO48-PTseq-Full-Process Reagent Bench Diagram(E25).jpg", "Remark": null}',NULL);
INSERT INTO workflow VALUES(686,'5','fa5f7e77-4005-434b-bafb-2e7f9896ab26','GenSIRO48-PTseq-提取（全流程E25）','code0000006','48提取','DeckScan','{"ScriptId": "", "ScriptName": "", "ScanString": "[{\"lane\": 1, \"pos\": 1, \"consumable\": \"1\", \"barcode\": null, \"position\": \"1\", \"barcode_number_type\": null, \"result\": \"1\", \"error_message\": null, \"is_row_valid\": false, \"IsSelect\": false, \"Sort\": 1, \"OrderIndex\": 1, \"Index\": 1, \"IsLocked\": false, \"ValidationBackgroundColor\": \"Transparent\", \"IsInputReadOnly\": false, \"sample_number\": null, \"IsScan\": false}]", "DeskData": "", "PositionParams": "", "PlateTypeAssociation": "Pretreatment"}',NULL);
INSERT INTO workflow VALUES(687,'6','fa5f7e77-4005-434b-bafb-2e7f9896ab26','GenSIRO48-PTseq-提取（全流程E25）','code0000005','Barcode录入','UpdateBarcodeId','{"SampleInfoProperty": "BarcodeId", "ScanString": "[{\"lane\": 1, \"pos\": 1, \"consumable\": \"1\", \"barcode\": null, \"position\": \"1\", \"barcode_number_type\": null, \"result\": \"1\", \"error_message\": null, \"is_row_valid\": false, \"IsSelect\": false, \"Sort\": 1, \"OrderIndex\": 1, \"Index\": 1, \"sample_number\": null, \"IsScan\": false}]"}',NULL);
INSERT INTO workflow VALUES(688,'7','fa5f7e77-4005-434b-bafb-2e7f9896ab26','GenSIRO48-PTseq-提取（全流程E25）','code0000006','48提取','ExecuteExperiment','{"ScriptId": "2025ec6a-8bac-4349-97bb-a93a6fc7d528", "ScriptName": "GenSIRO48-PTseq-提取", "ScanString": "", "DeskData": "", "PositionParams": "", "PlateTypeAssociation": "Pretreatment"}',NULL);
CREATE TABLE IF NOT EXISTS "sampleinfoproperty" (
  "id" text,
  "name" text,
  "value" TEXT,
  "table_value" TEXT
);
INSERT INTO sampleinfoproperty VALUES('1','样本编号','SampleNumber','sample_number');
INSERT INTO sampleinfoproperty VALUES('2','产品名称','ProductName','product_name');
INSERT INTO sampleinfoproperty VALUES('3','样本类型','SampleType','sample_type');
INSERT INTO sampleinfoproperty VALUES('4','质控类型','QcType','qc_type');
INSERT INTO sampleinfoproperty VALUES('5','前处理板号','PreptreatmentPlate','preptreatment_plate');
INSERT INTO sampleinfoproperty VALUES('6','前处理孔位','PreptreatmentWell','preptreatment_well');
INSERT INTO sampleinfoproperty VALUES('7','提取产物浓度','ExtractionQC','extraction_QC');
INSERT INTO sampleinfoproperty VALUES('8','提取产物荧光值','ExtractionSignal','extraction_signal');
INSERT INTO sampleinfoproperty VALUES('9','建库板号','LibprepPlate','libprep_plate');
INSERT INTO sampleinfoproperty VALUES('10','建库孔位','LibprepWell','libprep_well');
INSERT INTO sampleinfoproperty VALUES('11','建库产物浓度','LibprepQC','libprep_QC');
INSERT INTO sampleinfoproperty VALUES('12','建库产物荧光值','LibprepSignal','libprep_signal');
INSERT INTO sampleinfoproperty VALUES('13','杂洗板号','HybridPlate','hybrid_plate');
INSERT INTO sampleinfoproperty VALUES('14','杂洗孔位','HybridWell','hybrid_well');
INSERT INTO sampleinfoproperty VALUES('15','杂洗产物浓度','HybridQC','hybrid_QC');
INSERT INTO sampleinfoproperty VALUES('16','杂洗产物荧光值','HybridSignal','hybrid_signal');
INSERT INTO sampleinfoproperty VALUES('17','上机前准备板号','SeqprepPlate','seqprep_plate');
INSERT INTO sampleinfoproperty VALUES('18','上机前准备孔位','SeqprepWell','seqprep_well');
INSERT INTO sampleinfoproperty VALUES('19','DNB浓度','SeqprepQC','seqprep_QC');
INSERT INTO sampleinfoproperty VALUES('20','DNB荧光值','SeqprepSignal','seqprep_signal');
INSERT INTO sampleinfoproperty VALUES('21','BARCODE','BarcodeId','barcode_id');
INSERT INTO sampleinfoproperty VALUES('22','INDEX','SampleIndex','sample_index');
INSERT INTO sampleinfoproperty VALUES('23','UMI','Umi','umi');
INSERT INTO sampleinfoproperty VALUES('24','DNA取样体积','DnaVolume','dna_volume');
INSERT INTO sampleinfoproperty VALUES('25','DNA补水体积','DnaReplenishmentVolume','dna_replenishment_volume');
INSERT INTO sampleinfoproperty VALUES('26','子文库体积','LibraryVolume','library_volume');
INSERT INTO sampleinfoproperty VALUES('27','混合文库补水体积','PoolingReplenishmentVolume','pooling_replenishment_volume');
INSERT INTO sampleinfoproperty VALUES('28','混合文库编号','PoolingId','pooling_id');
INSERT INTO sampleinfoproperty VALUES('29','任务批次号','BatchNumber','batch_number');
INSERT INTO sampleinfoproperty VALUES('30','核酸类型','NucleicAcidsType','nucleic_acids_type');
INSERT INTO sampleinfoproperty VALUES('31','分析参数','AnalysisType','analysis_type');
INSERT INTO sampleinfoproperty VALUES('32','方案编号','FileID','file_ID');
CREATE TABLE IF NOT EXISTS "quantify_coefficient_type" (
  "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
  "coefficient_name" TEXT,
  "k1_value" TEXT,
  "k2_value" TEXT,
  "k3_value" TEXT,
  "k4_value" TEXT,
  "k5_value" TEXT,
  "k6_value" TEXT,
  "k7_value" TEXT,
  "k8_value" TEXT,
  "b1_value" TEXT,
  "b2_value" TEXT,
  "b3_value" TEXT,
  "b4_value" TEXT,
  "b5_value" TEXT,
  "b6_value" TEXT,
  "b7_value" TEXT,
  "b8_value" TEXT,
  "remark" TEXT
);
INSERT INTO quantify_coefficient_type VALUES(1,'DNA','34.54','34.54','34.54','34.54','34.54','34.54','34.54','34.54','189.65','189.65','189.65','189.65','189.65','189.65','189.65','189.65',NULL);
INSERT INTO quantify_coefficient_type VALUES(2,'DNB','18.22','18.22','18.22','18.22','18.22','18.22','18.22','18.22','78.57','78.57','78.57','78.57','78.57','78.57','78.57','78.57',NULL);
CREATE TABLE IF NOT EXISTS "sequencer" (
  "id" INTEGER,
  "sequencer" TEXT,
  "chip_type" TEXT,
  "max_data" TEXT,
  "remark" TEXT
);
INSERT INTO sequencer VALUES(1,'DNBSEQ-G99','FCL','80',NULL);
INSERT INTO sequencer VALUES(3,'MGISEQ-200','FCL','500',NULL);
INSERT INTO sequencer VALUES(4,'MGISEQ-200','FCS','100',NULL);
INSERT INTO sequencer VALUES(5,'MGISEQ-2000','FCL','400',NULL);
INSERT INTO sequencer VALUES(6,'MGISEQ-2000','FCS','275',NULL);
CREATE TABLE IF NOT EXISTS "worklist" (
  "id" text NOT NULL,
  "csv_name" text,
  "local_csv_path" TEXT,
  "remote_csv_path" text,
  "conditions" TEXT,
  "select_type" TEXT,
  "related_property" text,
  "param_value" TEXT,
  "source_position" TEXT,
  "source_consumable" text,
  "source_well" text,
  "volume" text,
  "target_position" TEXT,
  "target_consumable" text,
  "target_well" text,
  "remark" TEXT,
  PRIMARY KEY ("id"),
  UNIQUE ("csv_name" ASC)
);
INSERT INTO worklist VALUES('e391b78d-63a5-45a1-8c4a-52af53f41dfe','NIFTY加质控','D:\NIFTY\转移阴阳性对照品.csv','D:\NIFTY\转移阴阳性对照品.csv','[{"SelectType":"等于","SelectTypeName":"等于","RelatedProperty":"QcType","RelatedPropertyName":"质控类型","ParamValue":"N,P","OrderIndex":1,"IsSelect":false}]',NULL,NULL,NULL,'{"Type":"fix_value","ParamValue":"{\"Param1Value\":\"Rack8\",\"Param2Value\":null,\"Param3Value\":null,\"Param4Value\":null,\"Param5Value\":null,\"Param6Value\":null,\"Param7Value\":null,\"Param8Value\":null,\"Param9Value\":null,\"Param10Value\":null}"}','{"Type":"fix_value","ParamValue":"{\"Param1Value\":\"样本6-6-0.5ml管\",\"Param2Value\":null,\"Param3Value\":null,\"Param4Value\":null,\"Param5Value\":null,\"Param6Value\":null,\"Param7Value\":null,\"Param8Value\":null,\"Param9Value\":null,\"Param10Value\":null}"}','{"Type":"SIRO16_sample_property_value_equal","ParamValue":"{\"Param1Value\":\"QcType\",\"Param2Value\":\"P\",\"Param3Value\":\"D2\",\"Param4Value\":\"D1\",\"Param5Value\":null,\"Param6Value\":null,\"Param7Value\":null,\"Param8Value\":null,\"Param9Value\":null,\"Param10Value\":null}"}','{"Type":"fix_value","ParamValue":"{\"Param1Value\":\"2\",\"Param2Value\":null,\"Param3Value\":null,\"Param4Value\":null,\"Param5Value\":null,\"Param6Value\":null,\"Param7Value\":null,\"Param8Value\":null,\"Param9Value\":null,\"Param10Value\":null}"}','{"Type":"fix_value","ParamValue":"{\"Param1Value\":\"Rack2\",\"Param2Value\":null,\"Param3Value\":null,\"Param4Value\":null,\"Param5Value\":null,\"Param6Value\":null,\"Param7Value\":null,\"Param8Value\":null,\"Param9Value\":null,\"Param10Value\":null}"}','{"Type":"fix_value","ParamValue":"{\"Param1Value\":\"PCR仪\",\"Param2Value\":null,\"Param3Value\":null,\"Param4Value\":null,\"Param5Value\":null,\"Param6Value\":null,\"Param7Value\":null,\"Param8Value\":null,\"Param9Value\":null,\"Param10Value\":null}"}','{"Type":"SIRO16_sample_property","ParamValue":"{\"Param1Value\":\"PreptreatmentWell\",\"Param2Value\":null,\"Param3Value\":null,\"Param4Value\":null,\"Param5Value\":null,\"Param6Value\":null,\"Param7Value\":null,\"Param8Value\":null,\"Param9Value\":null,\"Param10Value\":null}"}',NULL);
INSERT INTO worklist VALUES('b8d43546-c402-4104-9ce5-7d1d3520f6ad','NIFTY_Pooling样本表','D:\NIFTY\pooling_2.csv','D:\NIFTY\pooling_2.csv','[{"SelectType":"等于","SelectTypeName":"等于","RelatedProperty":"QcType","RelatedPropertyName":"质控类型","ParamValue":"N,P,S","OrderIndex":1,"IsSelect":false}]',NULL,NULL,NULL,'{"Type":"fix_value","ParamValue":"{\"Param1Value\":\"Rack12\",\"Param2Value\":null,\"Param3Value\":null,\"Param4Value\":null,\"Param5Value\":null,\"Param6Value\":null,\"Param7Value\":null,\"Param8Value\":null,\"Param9Value\":null,\"Param10Value\":null}"}','{"Type":"fix_value","ParamValue":"{\"Param1Value\":\"半裙边PCR板\",\"Param2Value\":null,\"Param3Value\":null,\"Param4Value\":null,\"Param5Value\":null,\"Param6Value\":null,\"Param7Value\":null,\"Param8Value\":null,\"Param9Value\":null,\"Param10Value\":null}"}','{"Type":"SIRO16_sample_property","ParamValue":"{\"Param1Value\":\"LibprepWell\",\"Param2Value\":null,\"Param3Value\":null,\"Param4Value\":null,\"Param5Value\":null,\"Param6Value\":null,\"Param7Value\":null,\"Param8Value\":null,\"Param9Value\":null,\"Param10Value\":null}"}','{"Type":"SIRO16_sample_property","ParamValue":"{\"Param1Value\":\"LibraryVolume\",\"Param2Value\":null,\"Param3Value\":null,\"Param4Value\":null,\"Param5Value\":null,\"Param6Value\":null,\"Param7Value\":null,\"Param8Value\":null,\"Param9Value\":null,\"Param10Value\":null}"}','{"Type":"fix_value","ParamValue":"{\"Param1Value\":\"Rack6\",\"Param2Value\":null,\"Param3Value\":null,\"Param4Value\":null,\"Param5Value\":null,\"Param6Value\":null,\"Param7Value\":null,\"Param8Value\":null,\"Param9Value\":null,\"Param10Value\":null}"}','{"Type":"fix_value","ParamValue":"{\"Param1Value\":\"DeepHole\",\"Param2Value\":null,\"Param3Value\":null,\"Param4Value\":null,\"Param5Value\":null,\"Param6Value\":null,\"Param7Value\":null,\"Param8Value\":null,\"Param9Value\":null,\"Param10Value\":null}"}','{"Type":"SIRO16_sample_property","ParamValue":"{\"Param1Value\":\"SeqprepWell\",\"Param2Value\":null,\"Param3Value\":null,\"Param4Value\":null,\"Param5Value\":null,\"Param6Value\":null,\"Param7Value\":null,\"Param8Value\":null,\"Param9Value\":null,\"Param10Value\":null}"}',NULL);
INSERT INTO worklist VALUES('aabe4352-8fae-4580-86a1-bd3ee0f97808','NIFTY_Pooling补水表','D:\NIFTY\pooling_2-TE.csv','D:\NIFTY\pooling_2-TE.csv','[{"SelectType":"去重","SelectTypeName":"去重","RelatedProperty":"PoolingId","RelatedPropertyName":"混合文库编号","ParamValue":"","OrderIndex":1,"IsSelect":false}]',NULL,NULL,NULL,'{"Type":"fix_value","ParamValue":"{\"Param1Value\":\"Rack8\",\"Param2Value\":null,\"Param3Value\":null,\"Param4Value\":null,\"Param5Value\":null,\"Param6Value\":null,\"Param7Value\":null,\"Param8Value\":null,\"Param9Value\":null,\"Param10Value\":null}"}','{"Type":"fix_value","ParamValue":"{\"Param1Value\":\"样本6-6-0.5ml管\",\"Param2Value\":null,\"Param3Value\":null,\"Param4Value\":null,\"Param5Value\":null,\"Param6Value\":null,\"Param7Value\":null,\"Param8Value\":null,\"Param9Value\":null,\"Param10Value\":null}"}','{"Type":"fix_value","ParamValue":"{\"Param1Value\":\"19\",\"Param2Value\":null,\"Param3Value\":null,\"Param4Value\":null,\"Param5Value\":null,\"Param6Value\":null,\"Param7Value\":null,\"Param8Value\":null,\"Param9Value\":null,\"Param10Value\":null}"}','{"Type":"SIRO16_sample_property","ParamValue":"{\"Param1Value\":\"PoolingReplenishmentVolume\",\"Param2Value\":null,\"Param3Value\":null,\"Param4Value\":null,\"Param5Value\":null,\"Param6Value\":null,\"Param7Value\":null,\"Param8Value\":null,\"Param9Value\":null,\"Param10Value\":null}"}','{"Type":"fix_value","ParamValue":"{\"Param1Value\":\"Rack6\",\"Param2Value\":null,\"Param3Value\":null,\"Param4Value\":null,\"Param5Value\":null,\"Param6Value\":null,\"Param7Value\":null,\"Param8Value\":null,\"Param9Value\":null,\"Param10Value\":null}"}','{"Type":"fix_value","ParamValue":"{\"Param1Value\":\"DeepHole\",\"Param2Value\":null,\"Param3Value\":null,\"Param4Value\":null,\"Param5Value\":null,\"Param6Value\":null,\"Param7Value\":null,\"Param8Value\":null,\"Param9Value\":null,\"Param10Value\":null}"}','{"Type":"SIRO16_sample_property","ParamValue":"{\"Param1Value\":\"SeqprepWell\",\"Param2Value\":null,\"Param3Value\":null,\"Param4Value\":null,\"Param5Value\":null,\"Param6Value\":null,\"Param7Value\":null,\"Param8Value\":null,\"Param9Value\":null,\"Param10Value\":null}"}',NULL);
INSERT INTO worklist VALUES('064b5631-f318-425a-8f14-caa734537b3d','CNVSeq48','D:\CNVSeq\CNVSeq48.csv','D:\CNVSeq\CNVSeq48.csv','[{"SelectType":"去重","SelectTypeName":"去重","RelatedProperty":"SampleNumber","RelatedPropertyName":"样本编号","ParamValue":"","OrderIndex":1,"IsSelect":false}]',NULL,NULL,NULL,'{"Type":"fix_value","ParamValue":"{\"Param1Value\":\"Rack8\",\"Param2Value\":null,\"Param3Value\":null,\"Param4Value\":null,\"Param5Value\":null,\"Param6Value\":null,\"Param7Value\":null,\"Param8Value\":null,\"Param9Value\":null,\"Param10Value\":null}"}','{"Type":"fix_value","ParamValue":"{\"Param1Value\":\"样本6-6-0.5ml管\",\"Param2Value\":null,\"Param3Value\":null,\"Param4Value\":null,\"Param5Value\":null,\"Param6Value\":null,\"Param7Value\":null,\"Param8Value\":null,\"Param9Value\":null,\"Param10Value\":null}"}','{"Type":"fix_value","ParamValue":"{\"Param1Value\":\"19\",\"Param2Value\":null,\"Param3Value\":null,\"Param4Value\":null,\"Param5Value\":null,\"Param6Value\":null,\"Param7Value\":null,\"Param8Value\":null,\"Param9Value\":null,\"Param10Value\":null}"}','{"Type":"SIRO16_sample_property","ParamValue":"{\"Param1Value\":\"PoolingReplenishmentVolume\",\"Param2Value\":null,\"Param3Value\":null,\"Param4Value\":null,\"Param5Value\":null,\"Param6Value\":null,\"Param7Value\":null,\"Param8Value\":null,\"Param9Value\":null,\"Param10Value\":null}"}','{"Type":"fix_value","ParamValue":"{\"Param1Value\":\"Rack6\",\"Param2Value\":null,\"Param3Value\":null,\"Param4Value\":null,\"Param5Value\":null,\"Param6Value\":null,\"Param7Value\":null,\"Param8Value\":null,\"Param9Value\":null,\"Param10Value\":null}"}','{"Type":"fix_value","ParamValue":"{\"Param1Value\":\"DeepHole\",\"Param2Value\":null,\"Param3Value\":null,\"Param4Value\":null,\"Param5Value\":null,\"Param6Value\":null,\"Param7Value\":null,\"Param8Value\":null,\"Param9Value\":null,\"Param10Value\":null}"}','{"Type":"SIRO16_sample_property","ParamValue":"{\"Param1Value\":\"SeqprepWell\",\"Param2Value\":null,\"Param3Value\":null,\"Param4Value\":null,\"Param5Value\":null,\"Param6Value\":null,\"Param7Value\":null,\"Param8Value\":null,\"Param9Value\":null,\"Param10Value\":null}"}',NULL);
INSERT INTO worklist VALUES('a968d490-5242-407a-b69e-41d5a7136ca7','NIFTY48','D:\Nifty\NIFTY48.csv','D:\Nifty\NIFTY48.csv','[{"SelectType":"去重","SelectTypeName":"去重","RelatedProperty":"SampleNumber","RelatedPropertyName":"样本编号","ParamValue":"","OrderIndex":1,"IsSelect":false}]',NULL,NULL,NULL,'{"Type":"fix_value","ParamValue":"{\"Param1Value\":\"Rack8\",\"Param2Value\":null,\"Param3Value\":null,\"Param4Value\":null,\"Param5Value\":null,\"Param6Value\":null,\"Param7Value\":null,\"Param8Value\":null,\"Param9Value\":null,\"Param10Value\":null}"}','{"Type":"fix_value","ParamValue":"{\"Param1Value\":\"样本6-6-0.5ml管\",\"Param2Value\":null,\"Param3Value\":null,\"Param4Value\":null,\"Param5Value\":null,\"Param6Value\":null,\"Param7Value\":null,\"Param8Value\":null,\"Param9Value\":null,\"Param10Value\":null}"}','{"Type":"fix_value","ParamValue":"{\"Param1Value\":\"19\",\"Param2Value\":null,\"Param3Value\":null,\"Param4Value\":null,\"Param5Value\":null,\"Param6Value\":null,\"Param7Value\":null,\"Param8Value\":null,\"Param9Value\":null,\"Param10Value\":null}"}','{"Type":"SIRO16_sample_property","ParamValue":"{\"Param1Value\":\"PoolingReplenishmentVolume\",\"Param2Value\":null,\"Param3Value\":null,\"Param4Value\":null,\"Param5Value\":null,\"Param6Value\":null,\"Param7Value\":null,\"Param8Value\":null,\"Param9Value\":null,\"Param10Value\":null}"}','{"Type":"fix_value","ParamValue":"{\"Param1Value\":\"Rack6\",\"Param2Value\":null,\"Param3Value\":null,\"Param4Value\":null,\"Param5Value\":null,\"Param6Value\":null,\"Param7Value\":null,\"Param8Value\":null,\"Param9Value\":null,\"Param10Value\":null}"}','{"Type":"fix_value","ParamValue":"{\"Param1Value\":\"DeepHole\",\"Param2Value\":null,\"Param3Value\":null,\"Param4Value\":null,\"Param5Value\":null,\"Param6Value\":null,\"Param7Value\":null,\"Param8Value\":null,\"Param9Value\":null,\"Param10Value\":null}"}','{"Type":"SIRO16_sample_property","ParamValue":"{\"Param1Value\":\"SeqprepWell\",\"Param2Value\":null,\"Param3Value\":null,\"Param4Value\":null,\"Param5Value\":null,\"Param6Value\":null,\"Param7Value\":null,\"Param8Value\":null,\"Param9Value\":null,\"Param10Value\":null}"}',NULL);
CREATE TABLE IF NOT EXISTS "script" (
  "id" text NOT NULL,
  "script_name" text,
  "equipment_code" TEXT,
  "equipment" text,
  "experiment_name" text,
  "params_dictionarys" TEXT,
  "select_type" TEXT,
  "related_property" TEXT,
  "arg_value" text,
  "is_reset_tip" TEXT,
  "reset_tip_list" TEXT,
  "is_quantify" TEXT,
  "script_type" text,
  "pipette_csvname_list" text,
  "remark" text,
  PRIMARY KEY ("id")
);
INSERT INTO script VALUES('c37cd8c0-45da-4206-bfb6-b1280a066b51','NIFTY48提取','code0000006','48提取','NIFTY_中通量_提取_8-48反应_SIRO-48 V1.6','[]','去重','SampleNumber',NULL,'0','','0','NORM',NULL,NULL);
INSERT INTO script VALUES('1c525d05-f0e5-4b4f-91be-b72f8d50b5d3','NIFTY48建库','code0000007','48建库','NIFTY_中通量_建库_8-48反应_SIRO-48 V1.6','[{"ArgName":"样本","SelectType":"去重","SelectTypeName":"去重","RelatedProperty":"SampleNumber","RelatedPropertyName":"样本编号","ParamValue":"","OrderIndex":1,"IsSelect":false}]','去重','SampleNumber',NULL,'0','','0','PREP',NULL,NULL);
INSERT INTO script VALUES('b5616676-5243-4650-9471-fc6084ee8b80','NIFTY48上机前准备','code0000007','48建库','DNB','[]','去重','SampleNumber',NULL,'0','','0','PREP',NULL,NULL);
INSERT INTO script VALUES('d007de0c-c944-49f5-bcb2-4124bd0eb002','CNVSeq48提取','code0000006','48提取','CNVSeq_提取3.0','[{"ArgName":"SampleCount","SelectType":"去重","SelectTypeName":"去重","RelatedProperty":"SampleNumber","RelatedPropertyName":"样本编号","ParamValue":"","OrderIndex":1,"IsSelect":false}]','去重','SampleNumber',NULL,'0','','0','NORM',NULL,NULL);
INSERT INTO script VALUES('003e3b70-e2f3-4a08-8183-a7cf724407e0','CNVSeq48建库','code0000007','48建库','0531_CNVSeq_V7','[{"ArgName":"SampleCount","SelectType":"去重","SelectTypeName":"去重","RelatedProperty":"SampleNumber","RelatedPropertyName":"样本编号","ParamValue":"","OrderIndex":1,"IsSelect":false}]','去重','SampleNumber',NULL,'0','','0','PREP',NULL,NULL);
INSERT INTO script VALUES('367507f9-fc75-49f5-b0be-42224ef963bf','康孕提取_测试','code0000006','48提取','康孕提取v2','[{"ArgName":"SampleCount","SelectType":"去重","SelectTypeName":"去重","RelatedProperty":"SampleNumber","RelatedPropertyName":"样本编号","ParamValue":"","OrderIndex":1,"IsSelect":false}]','去重','SampleNumber',NULL,'0','','0','NORM',NULL,NULL);
INSERT INTO script VALUES('9c0441b6-a399-495f-a8f6-41768588192a','Siro48-NIFTY-提取-V1.8','code0000006','48提取','Siro48-NIFTY-提取-V1.8','[{"ArgName":"SampleCount","SelectType":"去重","SelectTypeName":"去重","RelatedProperty":"SampleNumber","RelatedPropertyName":"样本编号","ParamValue":"","OrderIndex":1,"IsSelect":false}]','去重','SampleNumber',NULL,'0','','0','NORM',NULL,NULL);
INSERT INTO script VALUES('7b3836ae-301e-4e9f-bc04-da2e3d927e58','Siro48-NIFTY-建库-V1.8','code0000007','48建库','Siro48-NIFTY-建库-V1.8','[{"ArgName":"SampleCount","SelectType":"去重","SelectTypeName":"去重","RelatedProperty":"SampleNumber","RelatedPropertyName":"样本编号","ParamValue":"","OrderIndex":1,"IsSelect":false}]','去重','SampleNumber',NULL,'0','','0','PREP',NULL,NULL);
INSERT INTO script VALUES('d273f089-0f3c-483a-a42b-48e44d16b86e','SIRO48开启温控','code0000007','48建库','开启温控','[{"ArgName":"样本","SelectType":"去重","SelectTypeName":"去重","RelatedProperty":"SampleNumber","RelatedPropertyName":"样本编号","ParamValue":"","OrderIndex":1,"IsSelect":false}]','去重','SampleNumber',NULL,'0','','0','PREP',NULL,NULL);
INSERT INTO script VALUES('4b99f7a0-5079-4b80-a21e-1e649bf790c9','SIRO48-DNB过夜','code0000007','48建库','DNB_Store_4C_Overnight','[{"ArgName":"样本","SelectType":"去重","SelectTypeName":"去重","RelatedProperty":"SampleNumber","RelatedPropertyName":"样本编号","ParamValue":"","OrderIndex":1,"IsSelect":false}]','去重','SampleNumber',NULL,'0','','0','PREP',NULL,NULL);
INSERT INTO script VALUES('2a6b67e4-a56c-4aae-859d-6808a1bd9502','康孕建库_测试','code0000007','48建库','0522_CNVSeq_V5','[{"ArgName":"SampleCount","SelectType":"去重","SelectTypeName":"去重","RelatedProperty":"SampleNumber","RelatedPropertyName":"样本编号","ParamValue":"","OrderIndex":1,"IsSelect":false}]','去重','SampleNumber',NULL,'0','','0','PREP',NULL,NULL);
CREATE TABLE IF NOT EXISTS "user" (
  "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
  "user_name" TEXT,
  "password" TEXT,
  "phone_number" text,
  "email" TEXT,
  "role_code" TEXT,
  "create_time" TEXT,
  "remark" TEXT
);
INSERT INTO user VALUES(1,'admin','admin',NULL,NULL,'1',NULL,NULL);
INSERT INTO user VALUES(2,'user','123456',NULL,NULL,'2',NULL,NULL);
CREATE TABLE IF NOT EXISTS "process" (
  "id" text NOT NULL,
  "process_name" TEXT,
  "product_start_well_number" TEXT,
  "inherit_process_type_value" TEXT,
  "process_type_value" TEXT,
  "is_harmonize_cen" TEXT,
  "harmonize_cen_condition_calculating" TEXT,
  "is_quantify" TEXT,
  "quantify_multiple" TEXT,
  "quantify_coefficient_value" TEXT,
  "is_pooling" TEXT,
  "pooling_start_well_number" TEXT,
  "remark" TEXT,
  PRIMARY KEY ("id")
);
INSERT INTO process VALUES('f33df7a7-e3b5-4830-bf74-3db4a911145a','GenSIRO48-PTseq-Extraction（FullProcess-G99&200）','1','','PreTreatment','0','[]','0','','','0','',NULL);
INSERT INTO process VALUES('ae66a0e8-32f6-4a3c-98bd-6862d1db80dc','GenSIRO48-PTseq-LibraryBuilding&SequencingPrep-E25','1','PreTreatment','LibraryPrep','0','[]','0','','','0','',NULL);
INSERT INTO process VALUES('3168b048-41af-4c36-991d-a93838750c0b','GenSIRO48-PTseq-LibraryBuilding&SequencingPrep-G99','1','PreTreatment','LibraryPrep','0','[]','0','','','0','',NULL);
INSERT INTO process VALUES('d981428e-9a8f-4fff-aebb-841cf48853f2','GenSIRO48-PTseq-LibraryBuilding&SequencingPrep-200','1','PreTreatment','LibraryPrep','0','[]','0','','','0','',NULL);
INSERT INTO process VALUES('da0bbb53-c5d7-4268-8939-69b8f743c921','GenSIRO48-PTseq-fake-SequencingPrep','1','LibraryPrep','SequencingPrep','0','[]','0','','','0','',NULL);
INSERT INTO process VALUES('eab536d5-e9e6-4332-b8a2-35e1718b1a4e','GenSIRO48-PTseq-Extraction（Pretreatment-Library）','1','','PreTreatment','0','[]','0','','','0','',NULL);
INSERT INTO process VALUES('b11875de-7bf3-43d9-98bd-ed349a9aa2f0','GenSIRO48-PTseq-LibraryBuilding','1','PreTreatment','LibraryPrep','0','[]','0','','','0','',NULL);
INSERT INTO process VALUES('7e95994e-09e2-4f42-8ecd-512d84f3a1c2','GenSIRO48-PTseq-SequencingPrep-E25','1','LibraryPrep','SequencingPrep','0','[]','0','','','0','',NULL);
INSERT INTO process VALUES('a830c028-f1bd-46cb-8b17-de09138e0eb5','GenSIRO48-PTseq-SequencingPrep-G99','1','LibraryPrep','SequencingPrep','0','[]','0','','','0','',NULL);
INSERT INTO process VALUES('84e67d61-e6cd-401a-bb5a-e3db66181bce','GenSIRO48-PTseq-SequencingPrep-200','1','LibraryPrep','SequencingPrep','0','[]','0','','','0','',NULL);
INSERT INTO process VALUES('003f01ca-bd44-4142-9a2f-e4ee87cba24b','GenSIRO48-Overnight','1','SequencingPrep','SaveProduct','0','[]','0','','','0','',NULL);
INSERT INTO process VALUES('d20649e5-f920-46f8-b2a2-3a58e29bdff0','SIRO48-DNB-Incubation','1','SequencingPrep','SaveProduct','0','[]','0','','','0','',NULL);
INSERT INTO process VALUES('fa5f7e77-4005-434b-bafb-2e7f9896ab26','GenSIRO48-PTseq-Extraction（FullProcess-E25）','1','','PreTreatment','0','[]','0','','','0','',NULL);
CREATE TABLE sequencer_product (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, product_name TEXT, analysis_type TEXT, sequencer TEXT, chip_type TEXT, sequencer_data TEXT, product_label_data TEXT, standard_library_volume TEXT, pooling_type TEXT, pooling_total_volume TEXT, total_volume TEXT, hybrid_mix_number TEXT, hybrid_mix_total_volume TEXT, remark TEXT);
INSERT INTO sequencer_product VALUES(1,'PMseq','1M','MGISEQ-200','FCL','41.6','20','21','1','200','48',NULL,NULL,NULL);
INSERT INTO sequencer_product VALUES(2,'PMseq','1M','DNBSEQ-G99','FCL','20','20','21','1','200','48',NULL,NULL,NULL);
INSERT INTO sequencer_product VALUES(3,'PMseq','1M','MGISEQ-2000','FCL','50','20','21','1','200','48',NULL,NULL,NULL);
INSERT INTO sequencer_product VALUES(4,'PTseq','1M','MGISEQ-2000','FCL','4.166','0.3','21','1','200','48',NULL,NULL,NULL);
INSERT INTO sequencer_product VALUES(5,'PTseq','1M','MGISEQ-200','FCL','4.166','0.3','21','1','200','48',NULL,NULL,NULL);
INSERT INTO sequencer_product VALUES(6,'PTseq','1M','DNBSEQ-G99','FCL','5','0.3','21','1','200','48',NULL,NULL,NULL);
INSERT INTO sequencer_product VALUES(7,'PMseq-D','1M','MGISEQ-200','FCL','41.6','20','21','1','200','48',NULL,NULL,NULL);
INSERT INTO sequencer_product VALUES(8,'PMseq-D','1M','DNBSEQ-G99','FCL','20','20','21','1','200','48',NULL,NULL,NULL);
INSERT INTO sequencer_product VALUES(9,'PMseq-D','1M','MGISEQ-2000','FCL','50','20','21','1','200','48',NULL,NULL,NULL);
INSERT INTO sequencer_product VALUES(10,'PMseq-R','1M','MGISEQ-200','FCL','41.6','20','21','1','200','48',NULL,NULL,NULL);
INSERT INTO sequencer_product VALUES(11,'PMseq-R','1M','DNBSEQ-G99','FCL','20','20','21','1','200','48',NULL,NULL,NULL);
INSERT INTO sequencer_product VALUES(12,'PMseq-R','1M','MGISEQ-2000','FCL','50','20','21','1','200','48',NULL,NULL,NULL);
INSERT INTO sequencer_product VALUES(13,'PTseq-RTI','1M','MGISEQ-2000','FCL','4.166','0.3','21','1','200','48',NULL,NULL,NULL);
INSERT INTO sequencer_product VALUES(14,'PTseq-RTI','1M','MGISEQ-200','FCL','4.166','0.3','21','1','200','48',NULL,NULL,NULL);
INSERT INTO sequencer_product VALUES(15,'PTseq-RTI','1M','DNBSEQ-G99','FCL','5','0.3','21','1','200','48',NULL,NULL,NULL);
INSERT INTO sequencer_product VALUES(16,'CNV-seq','1M','MGISEQ-2000','FCL','13.3','10','23','2','160','48',NULL,NULL,NULL);
INSERT INTO sequencer_product VALUES(17,'CNV-seq','100K','MGISEQ-2000','FCL','39.9','35','23','2','160','48',NULL,NULL,NULL);
INSERT INTO sequencer_product VALUES(18,'CNV-seq','1M','MGISEQ-200','FCL','10.4','10','23','2','160','48',NULL,NULL,NULL);
INSERT INTO sequencer_product VALUES(19,'CNV-seq','100K','MGISEQ-200','FCL','41.6','35','23','2','160','48',NULL,NULL,NULL);
INSERT INTO sequencer_product VALUES(20,'NIFTY','nifty','DNBSEQ-G99','FCL','6.66','6','30','2','160','48',NULL,NULL,NULL);
INSERT INTO sequencer_product VALUES(21,'NIFTY','nifty pro','DNBSEQ-G99','FCL','25','25','30','2','160','48',NULL,NULL,NULL);
INSERT INTO sequencer_product VALUES(22,'NIFTY','nifty','MGISEQ-2000','FCL','8.33','6','30','2','160','48',NULL,NULL,NULL);
INSERT INTO sequencer_product VALUES(23,'NIFTY','nifty pro','MGISEQ-2000','FCL','33.33','25','30','2','160','48',NULL,NULL,NULL);
INSERT INTO sequencer_product VALUES(24,'NIFTY','nifty','MGISEQ-200','FCL','10.4','6','30','2','160','48',NULL,NULL,NULL);
INSERT INTO sequencer_product VALUES(25,'NIFTY','nifty pro','MGISEQ-200','FCL','39.9','25','30','2','160','48',NULL,NULL,NULL);
INSERT INTO sequencer_product VALUES(26,'五癌','五癌','MGISEQ-2000','FCL','33.33','33.33','30','3','160','48','12','2000',NULL);
CREATE TABLE IF NOT EXISTS "siro48_script_info" (
  "id" TEXT,
  "script_name" TEXT NOT NULL,
  "equipment_code" TEXT NOT NULL,
  "experiment_name" TEXT NOT NULL,
  "description" TEXT,
  "create_time" TEXT,
  "update_time" TEXT,
  PRIMARY KEY ("id")
);
INSERT INTO siro48_script_info VALUES('2025ec6a-8bac-4349-97bb-a93a6fc7d528','GenSIRO48-PTseq-Extraction','code0000006','GenSIRO48-PTseq-Extraction',NULL,'2026-03-11 11:32:09','2026-03-11 11:33:31');
INSERT INTO siro48_script_info VALUES('69e1bcd1-fe87-4b40-a9d4-93637cedfc39','GenSIRO48-PTseq-LibraryBuilding&SequencingPrep-G99','code0000007','GenSIRO48-PTseq-LibraryBuilding&SequencingPrep-G99',NULL,'2026-03-11 11:33:52','2026-03-11 14:41:17');
INSERT INTO siro48_script_info VALUES('aee82507-2a98-41de-a5be-823577f065ac','GenSIRO48-PTseq-LibraryBuilding&SequencingPrep-2000&200','code0000007','GenSIRO48-PTseq-LibraryBuilding&SequencingPrep-2000&200',NULL,'2026-03-11 14:41:23','2026-03-11 14:42:30');
INSERT INTO siro48_script_info VALUES('a09f6afe-95f3-427c-8d7d-e644f2e4ce83','GenSIRO48-PTseq-LibraryBuilding&SequencingPrep-E25','code0000007','GenSIRO48-PTseq-LibraryBuilding&SequencingPrep-E25',NULL,'2026-03-11 14:42:37','2026-03-11 14:43:10');
INSERT INTO siro48_script_info VALUES('27e2a5bb-3fc7-4565-b807-7ef90200d99b','GenSIRO48-PTseq-SequencingPrep-G99','code0000007','GenSIRO48-PTseq-SequencingPrep-G99',NULL,'2026-03-11 14:45:22','2026-03-11 14:46:18');
INSERT INTO siro48_script_info VALUES('8ec0aa83-2ef6-4706-94a6-3f0aec99dcf9','GenSIRO48-PTseq-SequencingPrep-E25','code0000007','GenSIRO48-PTseq-SequencingPrep-E25',NULL,'2026-03-11 14:46:23','2026-03-11 14:46:36');
INSERT INTO siro48_script_info VALUES('11547208-aef4-42e6-9061-1d2a9dea720a','GenSIRO48-PTseq-SequencingPrep-2000&200','code0000007','GenSIRO48-PTseq-SequencingPrep-2000&200',NULL,'2026-03-11 14:46:40','2026-03-11 14:47:03');
INSERT INTO siro48_script_info VALUES('ab8eba8f-a258-4b05-9ddb-287678a4adc8','GenSIRO48-PTseq-DNB-Overnight','code0000007','GenSIRO48-PTseq-DNB-Overnight',NULL,'2026-03-11 16:06:01','2026-03-11 16:06:32');
INSERT INTO siro48_script_info VALUES('cc5f0fa6-81fa-427f-a754-48a587116279','GenSIRO48-PTseq-Temperature_Control','code0000007','GenSIRO48-PTseq-Temperature_Control',NULL,'2026-03-11 16:06:34','2026-03-11 16:07:02');
INSERT INTO siro48_script_info VALUES('47f2bf6c-a6d3-405e-a3a9-65ab8ae84f2d','GenSIRO48-PTseq-LibraryBuilding','code0000007','GenSIRO48-PTseq-LibraryBuilding',NULL,'2026-03-26 16:17:18','2026-03-26 16:17:18');
INSERT INTO siro48_script_info VALUES('5468c284-39a6-4370-919a-36714e9160bb','GenSIRO48-PTseq-fake_dnb','code0000007','GenSIRO48-PTseq-fake_dnb',NULL,'2026-03-26 16:17:18','2026-03-26 16:17:18');
INSERT INTO siro48_script_info VALUES('29051113-3662-43aa-877d-56c750bebee3','GenSIRO48-PTseq-DNB-Incubation','code0000007','GenSIRO48-PTseq-DNB-Incubation',NULL,'2026-03-26 16:17:18','2026-03-26 16:17:18');
CREATE TABLE IF NOT EXISTS "siro48_script_table_mapping" (
  "id" TEXT,
  "script_info_id" TEXT NOT NULL,
  "table_config_id" TEXT NOT NULL,
  "order_index" INTEGER,
  PRIMARY KEY ("id")
);
INSERT INTO siro48_script_table_mapping VALUES('adb25255-a4a7-42b3-8f8a-2234e3cd7f4c','69e1bcd1-fe87-4b40-a9d4-93637cedfc39','376c5abf-c5f3-4781-a6a7-268659a482b9',2);
INSERT INTO siro48_script_table_mapping VALUES('4944ec4b-2bf4-4c61-a2c5-cbf1822a4ce9','69e1bcd1-fe87-4b40-a9d4-93637cedfc39','13f49971-63b2-4b98-98af-9b452325c280',3);
INSERT INTO siro48_script_table_mapping VALUES('90c16405-630f-40d2-ade1-29b6e9bc4bd2','aee82507-2a98-41de-a5be-823577f065ac','376c5abf-c5f3-4781-a6a7-268659a482b9',2);
INSERT INTO siro48_script_table_mapping VALUES('db6214c4-7957-4fe7-be06-c17ffca41197','aee82507-2a98-41de-a5be-823577f065ac','13f49971-63b2-4b98-98af-9b452325c280',3);
INSERT INTO siro48_script_table_mapping VALUES('35cf88a5-50a9-48e8-85dc-951892f545d3','a09f6afe-95f3-427c-8d7d-e644f2e4ce83','376c5abf-c5f3-4781-a6a7-268659a482b9',2);
INSERT INTO siro48_script_table_mapping VALUES('7ad1f2bb-69d5-4e5d-bba9-e9fe5d4e13da','a09f6afe-95f3-427c-8d7d-e644f2e4ce83','13f49971-63b2-4b98-98af-9b452325c280',3);
INSERT INTO siro48_script_table_mapping VALUES('86442893-7b4d-47bd-94fa-15ebd8a8f5c8','27e2a5bb-3fc7-4565-b807-7ef90200d99b','257331d8-36cb-44a1-bd10-ed6e8d4be983',1);
INSERT INTO siro48_script_table_mapping VALUES('14ca255f-ef5f-477d-9858-c9e868fa3087','27e2a5bb-3fc7-4565-b807-7ef90200d99b','c396b882-532d-4c28-ad43-90fb89b1a292',2);
INSERT INTO siro48_script_table_mapping VALUES('46377d75-21ae-4728-a261-f930183b3747','8ec0aa83-2ef6-4706-94a6-3f0aec99dcf9','257331d8-36cb-44a1-bd10-ed6e8d4be983',1);
INSERT INTO siro48_script_table_mapping VALUES('ad674924-3361-4df0-8238-ff70cb3b9ed1','8ec0aa83-2ef6-4706-94a6-3f0aec99dcf9','c396b882-532d-4c28-ad43-90fb89b1a292',3);
INSERT INTO siro48_script_table_mapping VALUES('2f9bf995-83aa-4c1a-b601-fdf8ecd397b9','11547208-aef4-42e6-9061-1d2a9dea720a','257331d8-36cb-44a1-bd10-ed6e8d4be983',1);
INSERT INTO siro48_script_table_mapping VALUES('1f84950d-8e12-4d61-9ea2-4c77f2db536a','11547208-aef4-42e6-9061-1d2a9dea720a','c396b882-532d-4c28-ad43-90fb89b1a292',4);
INSERT INTO siro48_script_table_mapping VALUES('c0740377-1037-49c6-8638-931c10543112','47f2bf6c-a6d3-405e-a3a9-65ab8ae84f2d','26d160f5-8e4f-440c-80f1-6d1248962c80',1);
INSERT INTO siro48_script_table_mapping VALUES('b3e367b2-410e-492e-b51c-3cd08a8fa1ef','47f2bf6c-a6d3-405e-a3a9-65ab8ae84f2d','376c5abf-c5f3-4781-a6a7-268659a482b9',2);
INSERT INTO siro48_script_table_mapping VALUES('151127a4-d51b-41c7-a09b-5f1fa4bdce98','2025ec6a-8bac-4349-97bb-a93a6fc7d528','42ead651-83df-4c1d-b0d5-74156a7cb3c5',1);
INSERT INTO siro48_script_table_mapping VALUES('71f7729d-5471-4618-ad44-9bcbb5243502','69e1bcd1-fe87-4b40-a9d4-93637cedfc39','26d160f5-8e4f-440c-80f1-6d1248962c80',1);
INSERT INTO siro48_script_table_mapping VALUES('f9806fca-58c1-46e4-86ed-ff0cedde1151','a09f6afe-95f3-427c-8d7d-e644f2e4ce83','26d160f5-8e4f-440c-80f1-6d1248962c80',1);
INSERT INTO siro48_script_table_mapping VALUES('f66bcdb8-f402-432e-948d-edcd55b46a59','aee82507-2a98-41de-a5be-823577f065ac','26d160f5-8e4f-440c-80f1-6d1248962c80',1);
CREATE TABLE IF NOT EXISTS "siro48_table_config" (
  "id" TEXT,
  "table_name" TEXT NOT NULL,
  "table_type" TEXT NOT NULL,
  "table_path" TEXT NOT NULL,
  "fields_config" TEXT,
  "description" TEXT,
  "create_time" TEXT,
  "update_time" TEXT,
  PRIMARY KEY ("id")
);
INSERT INTO siro48_table_config VALUES('42ead651-83df-4c1d-b0d5-74156a7cb3c5','GenSIRO48-PTseq-输入表格','Input','D:\Pathogens\PTseq.csv','[{"SampleInfoProperty":"SampleNumber","ColumnIndex":1},{"SampleInfoProperty":"PreptreatmentWell","ColumnIndex":2},{"SampleInfoProperty":"PreptreatmentPlate","ColumnIndex":3},{"SampleInfoProperty":"QcType","ColumnIndex":4},{"SampleInfoProperty":"ProductName","ColumnIndex":5},{"SampleInfoProperty":"BarcodeId","ColumnIndex":6},{"SampleInfoProperty":"SampleType","ColumnIndex":7}]',NULL,'2026-03-11 09:18:47','2026-03-26 16:30:00');
INSERT INTO siro48_table_config VALUES('257331d8-36cb-44a1-bd10-ed6e8d4be983','GenSIRO48-PTseq-上机前准备输入表格','Input','D:\Pathogens\PTseq_concentration.csv','[{"SampleInfoProperty": "SampleNumber", "ColumnIndex": 1}, {"SampleInfoProperty": "LibprepWell", "ColumnIndex": 2}, {"SampleInfoProperty": "LibprepPlate", "ColumnIndex": 3}, {"SampleInfoProperty": "LibprepQC", "ColumnIndex": 4}, {"SampleInfoProperty": "AnalysisType", "ColumnIndex": 5}, {"SampleInfoProperty": "BarcodeId", "ColumnIndex": 6}, {"SampleInfoProperty": "QcType", "ColumnIndex": 7}]',NULL,'2026-03-11 09:35:55','2026-03-26 16:30:00');
INSERT INTO siro48_table_config VALUES('376c5abf-c5f3-4781-a6a7-268659a482b9','GenSIRO48-PTseq-建库输出表格','Output','D:\data\PTseq_Library.xlsx','[{"SampleInfoProperty": "LibprepQC", "ColumnIndex": 5}]',NULL,'2026-03-11 09:48:25','2026-03-26 16:17:18');
INSERT INTO siro48_table_config VALUES('13f49971-63b2-4b98-98af-9b452325c280','GenSIRO48-PTseq-LibraryBuilding-Pooling-output-form','Output','D:\data\PTseq_pooling_info.csv','[{"SampleInfoProperty":"PoolingId","ColumnIndex":2},{"SampleInfoProperty":"LibraryVolume","ColumnIndex":3}]',NULL,'2026-03-11 10:53:10','2026-07-12 00:00:00');
INSERT INTO siro48_table_config VALUES('c396b882-532d-4c28-ad43-90fb89b1a292','GenSIRO48-PTseq-SequencingPrep-Pooling-output-form','Output','D:\data\PTseq_pooling_info.csv','[{"SampleInfoProperty":"PoolingId","ColumnIndex":2},{"SampleInfoProperty":"LibraryVolume","ColumnIndex":3}]',NULL,'2026-03-11 11:02:34','2026-03-11 11:05:25');
INSERT INTO siro48_table_config VALUES('26d160f5-8e4f-440c-80f1-6d1248962c80','GenSIRO48-PTseq-LibraryBuilding-input-form','Input','D:\Pathogens\PTseq.csv','[{"SampleInfoProperty": "SampleNumber", "ColumnIndex": 1}, {"SampleInfoProperty": "PreptreatmentWell", "ColumnIndex": 2}, {"SampleInfoProperty": "PreptreatmentPlate", "ColumnIndex": 3}, {"SampleInfoProperty": "QcType", "ColumnIndex": 4}, {"SampleInfoProperty": "ProductName", "ColumnIndex": 5}, {"SampleInfoProperty": "BarcodeId", "ColumnIndex": 6}, {"SampleInfoProperty": "SampleType", "ColumnIndex": 7}]',NULL,'2026-03-26 16:17:18','2026-03-26 16:30:00');
CREATE TABLE product (id text, file_ID TEXT, product_class text, show_product_class TEXT, test_name TEXT, technical_route text, show_technical_route text, experimental_stage text, show_experimental_stage TEXT, sequencer TEXT, chip_type TEXT, is_permit text, process_id_list TEXT, max_count TEXT, start_property TEXT, is_pooling TEXT, remark text, min_count TEXT);
INSERT INTO product VALUES('7f732593-0569-46ec-8589-3f658de2c54e','PTseq001','PTseq','PTseq','PTseq','PTseq','PTseq','Full-process','Full-process','DNBSEQ-E25','FCL','Yes','fa5f7e77-4005-434b-bafb-2e7f9896ab26;ae66a0e8-32f6-4a3c-98bd-6862d1db80dc;da0bbb53-c5d7-4268-8939-69b8f743c921;003f01ca-bd44-4142-9a2f-e4ee87cba24b','48','SampleNumber','0',NULL,'5');
INSERT INTO product VALUES('2e61c7a3-bfcc-4640-8e9c-ba60e2bda834','PTseq002','PTseq','PTseq','PTseq','PTseq','PTseq','Full-process','Full-process','DNBSEQ-G99','FCL','Yes','f33df7a7-e3b5-4830-bf74-3db4a911145a;3168b048-41af-4c36-991d-a93838750c0b;da0bbb53-c5d7-4268-8939-69b8f743c921;003f01ca-bd44-4142-9a2f-e4ee87cba24b','48','SampleNumber','0',NULL,'5');
INSERT INTO product VALUES('3e3d4333-8a93-4d6e-be16-2d88a245aff8','PTseq003','PTseq','PTseq','PTseq','PTseq','PTseq','Full-process','Full-process','MGISEQ-200','FCL','Yes','f33df7a7-e3b5-4830-bf74-3db4a911145a;d981428e-9a8f-4fff-aebb-841cf48853f2;da0bbb53-c5d7-4268-8939-69b8f743c921;003f01ca-bd44-4142-9a2f-e4ee87cba24b','48','SampleNumber','0',NULL,'5');
INSERT INTO product VALUES('c93f8831-2071-4eb1-8541-dd9342e7c1f3','PTseq004','PTseq','PTseq','PTseq','PTseq','PTseq','Pretreatment-LibraryPrep','Pretreatment-LibraryPrep','DNBSEQ-E25','FCL','Yes','eab536d5-e9e6-4332-b8a2-35e1718b1a4e;b11875de-7bf3-43d9-98bd-ed349a9aa2f0;d20649e5-f920-46f8-b2a2-3a58e29bdff0','48','SampleNumber','0',NULL,'5');
INSERT INTO product VALUES('618ade7b-80f8-4151-91c5-d19a1ef5200e','PTseq005','PTseq','PTseq','PTseq','PTseq','PTseq','Pretreatment-LibraryPrep','Pretreatment-LibraryPrep','DNBSEQ-G99','FCL','Yes','eab536d5-e9e6-4332-b8a2-35e1718b1a4e;b11875de-7bf3-43d9-98bd-ed349a9aa2f0;d20649e5-f920-46f8-b2a2-3a58e29bdff0','48','SampleNumber','0',NULL,'5');
INSERT INTO product VALUES('c5616d0a-2d03-49ea-b57f-9752c96b33fb','PTseq006','PTseq','PTseq','PTseq','PTseq','PTseq','Pretreatment-LibraryPrep','Pretreatment-LibraryPrep','MGISEQ-200','FCL','Yes','eab536d5-e9e6-4332-b8a2-35e1718b1a4e;b11875de-7bf3-43d9-98bd-ed349a9aa2f0;d20649e5-f920-46f8-b2a2-3a58e29bdff0','48','SampleNumber','0',NULL,'5');
INSERT INTO product VALUES('c93d2db4-b888-456f-b77e-4c0173762989','PTseq007','PTseq','PTseq','PTseq','PTseq','PTseq','SequencingPrep','SequencingPrep','DNBSEQ-E25','FCL','Yes','7e95994e-09e2-4f42-8ecd-512d84f3a1c2;003f01ca-bd44-4142-9a2f-e4ee87cba24b','192','SampleNumber','0',NULL,'1');
INSERT INTO product VALUES('15d971b9-5d1a-4d71-9825-2511857d55d9','PTseq008','PTseq','PTseq','PTseq','PTseq','PTseq','SequencingPrep','SequencingPrep','DNBSEQ-G99','FCL','Yes','a830c028-f1bd-46cb-8b17-de09138e0eb5;003f01ca-bd44-4142-9a2f-e4ee87cba24b','192','SampleNumber','0',NULL,'1');
INSERT INTO product VALUES('6da73ab1-a06c-404d-8dd9-4dca62e27ded','PTseq009','PTseq','PTseq','PTseq','PTseq','PTseq','SequencingPrep','SequencingPrep','MGISEQ-200','FCL','Yes','84e67d61-e6cd-401a-bb5a-e3db66181bce;003f01ca-bd44-4142-9a2f-e4ee87cba24b','192','SampleNumber','0',NULL,'1');
INSERT INTO product VALUES('f8eedcfc-7939-417c-9589-119ad1c40d34','PTseq003','PTseq','PTseq','PTseq','PTseq','PTseq','Full-process','Full-process','MGISEQ-2000','FCL','Yes','f33df7a7-e3b5-4830-bf74-3db4a911145a;d981428e-9a8f-4fff-aebb-841cf48853f2;da0bbb53-c5d7-4268-8939-69b8f743c921;003f01ca-bd44-4142-9a2f-e4ee87cba24b','48','SampleNumber','0',NULL,'5');
INSERT INTO product VALUES('bb2413b9-10c4-4248-a5bf-1d0d7ac3cbe0','PTseq006','PTseq','PTseq','PTseq','PTseq','PTseq','Pretreatment-LibraryPrep','Pretreatment-LibraryPrep','MGISEQ-2000','FCL','Yes','eab536d5-e9e6-4332-b8a2-35e1718b1a4e;b11875de-7bf3-43d9-98bd-ed349a9aa2f0;d20649e5-f920-46f8-b2a2-3a58e29bdff0','48','SampleNumber','0',NULL,'5');
INSERT INTO product VALUES('d0cc3013-589a-4a1b-a3db-e4e10019f82b','PTseq009','PTseq','PTseq','PTseq','PTseq','PTseq','SequencingPrep','SequencingPrep','MGISEQ-2000','FCL','Yes','84e67d61-e6cd-401a-bb5a-e3db66181bce;003f01ca-bd44-4142-9a2f-e4ee87cba24b','192','SampleNumber','0',NULL,'1');
INSERT INTO sqlite_sequence VALUES('script_worklist',161);
INSERT INTO sqlite_sequence VALUES('equipment',7);
INSERT INTO sqlite_sequence VALUES('workflow',688);
INSERT INTO sqlite_sequence VALUES('quantify_coefficient_type','2');
INSERT INTO sqlite_sequence VALUES('user','2');
INSERT INTO sqlite_sequence VALUES('sequencer_product',26);
COMMIT;
