# Future capability catalog

This document records the capability families Mirror is designed to host.

It is a catalog, not a commitment schedule.

Mirror's kernel stays general-purpose. The capability families below may be built now, later, by the core team, or by third-party contributors. Any vendor-specific provider must remain optional and replaceable.

## Open-source-first provider defaults

The first-party ecosystem should prefer self-hostable or open-source-friendly providers such as:
- Ollama
- sentence-transformers
- pgvector
- Qdrant
- Milvus
- Weaviate
- Chroma
- Camoufox
- SeleniumBase UC
- Playwright
- Tesseract
- PyMuPDF
- pdfplumber
- Camelot
- Tabula
- dbt-style SQL transforms
- OpenCV
- FFmpeg
- OpenTelemetry
- Prometheus
- ClamAV
- Presidio
- SpaCy / Med7
- OpenStreetMap / Nominatim / OSRM / GraphHopper
- OpenAI-compatible provider APIs only as optional third-party plugins, not as core dependencies

Proprietary vendors may appear only as optional community plugins or external adapters.

## Near-future ecosystem families

### Document intelligence and OCR
- `mirror_ocr` — Optical Character Recognition
- `mirror_pdf` — native PDF text/layout extraction
- `mirror_table_extract` — table extraction from PDFs, HTML, and images
- `mirror_image_process` — image preprocessing for OCR and document pipelines
- `mirror_document_parse` — generic document parsing and normalization

### Browser, stealth, and network access
- `mirror_stealth` — fingerprint shaping and anti-detection helpers
- `mirror_proxy_manager` — proxy pools, rotation, and health checks
- `mirror_rpa_engine` — state-machine automation and human escalation
- `mirror_agent_crawl` — agentic or LLM-guided link selection
- `mirror_webhook_gateway` — webhook receivers and forwarders

### Knowledge preparation
- `mirror_llm_parse` — structured extraction from unstructured text
- `mirror_chunk` expansions — semantic, recursive, and document-aware chunking
- `mirror_dedup` expansions — MinHash, SimHash, embedding similarity
- `mirror_embed` expansions — local and self-hosted embedding providers
- `mirror_vector` expansions — local and self-hosted vector backends
- `mirror_retrieval` expansions — hybrid, rerank, and lexical/vector fusion
- `mirror_privacy_guard` — PII redaction and privacy filters
- `mirror_provenance` expansions — lineage, traceability, and source tracking

### Operational and platform support
- `mirror_airflow_sync` — DAG generation and sync
- `mirror_k8s_orch` — Kubernetes operators and Helm generation
- `mirror_otel_metrics` — metrics and tracing exporters
- `mirror_email_verify` — email verification helpers
- `mirror_geo_maps` — maps and places workflows for APIs and tiles
- `mirror_social_collect` — read-only public social data collection
- `mirror_real_estate` — listing aggregation
- `mirror_gov_portal` — session-based portal scraping helpers

## Far-future domain families

### Bioinformatics and life sciences
- `mirror_dna_align`
- `mirror_protein_fold`
- `mirror_spectra_analyze`
- `mirror_cell_count`
- `mirror_vcf_parse`
- `mirror_medical_ner`
- `mirror_dicom_read`
- `mirror_pharma_drug_interact`

### Finance and quantitative trading
- `mirror_tick_feed`
- `mirror_trade_exec`
- `mirror_risk_calc`
- `mirror_portfolio_balance`
- `mirror_option_pricing`
- `mirror_fraud_detect`
- `mirror_credit_score`
- `mirror_invoice_reconcile`
- `mirror_tax_calc`
- `mirror_sec_filing_parse`

### Industrial IoT and manufacturing
- `mirror_sensor_read`
- `mirror_serial`
- `mirror_ble_scan`
- `mirror_zigbee`
- `mirror_mqtt_sub`
- `mirror_lora`
- `mirror_actuator_control`
- `mirror_plc_read`
- `mirror_scada_log`

### Multimedia and creative
- `mirror_audio_transcribe`
- `mirror_audio_analyze`
- `mirror_video_trim`
- `mirror_video_analyze`
- `mirror_face_detect`
- `mirror_object_detect`
- `mirror_depth_map`

### Database and ETL beyond web APIs
- `mirror_db_export`
- `mirror_db_migrate`
- `mirror_cdc_read`
- `mirror_data_transform`
- `mirror_snowflake_load`
- `mirror_bigquery_load`
- `mirror_delta_sync`
- `mirror_data_quality`
- `mirror_master_data`

### Desktop and operating-system automation
- `mirror_watch_folder`
- `mirror_compress`
- `mirror_encrypt`
- `mirror_decrypt`
- `mirror_file_move`
- `mirror_file_delete`
- `mirror_shell_exec`
- `mirror_clipboard_read`
- `mirror_clipboard_write`
- `mirror_desktop_click`

### Network and systems beyond HTTP
- `mirror_ping`
- `mirror_traceroute`
- `mirror_dns_resolve`
- `mirror_ssh_exec`
- `mirror_scp`
- `mirror_sftp`
- `mirror_port_scan`
- `mirror_bandwidth_test`

### AI / ML engineering beyond RAG
- `mirror_classify`
- `mirror_segment`
- `mirror_train`
- `mirror_hyperopt`
- `mirror_feature_store`
- `mirror_model_serve`
- `mirror_drift_detect`
- `mirror_ab_test`
- `mirror_recommend`
- `mirror_anomaly_detect`

### Blockchain and Web3 off-chain data
- `mirror_chain_read`
- `mirror_tx_submit`
- `mirror_contract_call`
- `mirror_wallet_create`
- `mirror_merkle_proof`
- `mirror_ipfs_pin`
- `mirror_ipfs_get`

### Geospatial and physical logistics
- `mirror_gps_read`
- `mirror_geo_fence`
- `mirror_elevation_get`
- `mirror_route_calc`
- `mirror_traffic_analyze`
- `mirror_weather_get`
- `mirror_grid_tile`

### Messaging and collaboration
- `mirror_slack_read`
- `mirror_teams_read`
- `mirror_email_imap`
- `mirror_email_smtp_send`
- `mirror_jira_read`
- `mirror_confluence_read`

### Legacy and mainframe
- `mirror_cobol_parse`
- `mirror_edifact_read`
- `mirror_fixed_width_read`
- `mirror_ebcdic_convert`
- `mirror_vsam_read`
- `mirror_jcl_parse`

### Data privacy and security
- `mirror_hash_crack`
- `mirror_password_check`
- `mirror_virus_scan`
- `mirror_metadata_strip`
- `mirror_entropy_check`
- `mirror_cert_check`

### Scientific computing
- `mirror_fem_sim`
- `mirror_cfd_sim`
- `mirror_astro_calibrate`
- `mirror_weather_forecast`
- `mirror_seismic_detect`
- `mirror_particle_sim`

## Policy notes

- The catalog above does not imply every package will be first-party.
- Mirror should remain open-source-first and vendor-neutral.
- Third-party plugins may implement any of these contracts if they obey the kernel rules.
- Proprietary provider names should never become core dependencies.
- If a future package cannot be expressed as a capability contract plus provider implementation, it does not belong in Mirror.

## Reading guide

- Use the architecture document for ownership and dependency rules.
- Use ADRs for decisions that change the kernel.
- Use this catalog for long-range ecosystem planning.
- Use roadmap docs for what the team is actually building next.
