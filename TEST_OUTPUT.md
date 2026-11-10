Command: .\.venv\Scripts\python.exe manage.py test --verbosity 2

Found 42 test(s).
Operations to perform:
  Synchronize unmigrated apps: messages, staticfiles
  Apply all migrations: admin, auth, catalog, contenttypes, fulfillment, sessions
Synchronizing apps without migrations:
  Creating tables...
    Running deferred SQL...
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying auth.0001_initial... OK
  Applying admin.0001_initial... OK
  Applying admin.0002_logentry_remove_auto_add... OK
  Applying admin.0003_logentry_add_action_flag_choices... OK
  Applying contenttypes.0002_remove_content_type_name... OK
  Applying auth.0002_alter_permission_name_max_length... OK
  Applying auth.0003_alter_user_email_max_length... OK
  Applying auth.0004_alter_user_username_opts... OK
  Applying auth.0005_alter_user_last_login_null... OK
  Applying auth.0006_require_contenttypes_0002... OK
  Applying auth.0007_alter_validators_add_error_messages... OK
  Applying auth.0008_alter_user_username_max_length... OK
  Applying auth.0009_alter_user_last_name_max_length... OK
  Applying auth.0010_alter_group_name_max_length... OK
  Applying auth.0011_update_proxy_permissions... OK
  Applying auth.0012_alter_user_first_name_max_length... OK
  Applying catalog.0001_initial... OK
  Applying fulfillment.0001_initial... OK
  Applying sessions.0001_initial... OK
System check identified no issues (0 silenced).
Creating test database for alias 'default' ('file:memorydb_default?mode=memory&cache=shared')...

test_catalog_scenarios (fulfillment.tests.test_demo.DemoRecommendationTests.test_catalog_scenarios) ... ok
test_command_recommends_the_mailer_and_can_save (fulfillment.tests.test_demo.DemoRecommendationTests.test_command_recommends_the_mailer_and_can_save) ... ok
test_command_rejects_a_bad_token_and_an_unknown_sku (fulfillment.tests.test_demo.DemoRecommendationTests.test_command_rejects_a_bad_token_and_an_unknown_sku) ... ok
test_dumbbell_is_too_heavy_for_the_medium_box (fulfillment.tests.test_demo.DemoRecommendationTests.test_dumbbell_is_too_heavy_for_the_medium_box) ... ok
test_kettlebell_reports_size_before_weight_on_the_small_box (fulfillment.tests.test_demo.DemoRecommendationTests.test_kettlebell_reports_size_before_weight_on_the_small_box) ... ok
test_seed_is_idempotent (fulfillment.tests.test_demo.DemoRecommendationTests.test_seed_is_idempotent) ... ok
test_page_explains_how_to_load_demo_data (fulfillment.tests.test_http.EmptyCatalogTests.test_page_explains_how_to_load_demo_data) ... ok
test_an_unfulfillable_order_can_be_saved (fulfillment.tests.test_http.WarehouseHttpTests.test_an_unfulfillable_order_can_be_saved) ... ok
test_api_merges_duplicate_skus_and_can_save (fulfillment.tests.test_http.WarehouseHttpTests.test_api_merges_duplicate_skus_and_can_save) ... ok
test_api_recommends_a_phone_mailer (fulfillment.tests.test_http.WarehouseHttpTests.test_api_recommends_a_phone_mailer) ... ok
test_api_rejects_bad_input (fulfillment.tests.test_http.WarehouseHttpTests.test_api_rejects_bad_input) ... ok
test_blank_negative_and_text_quantities_are_rejected (fulfillment.tests.test_http.WarehouseHttpTests.test_blank_negative_and_text_quantities_are_rejected) ... ok
test_catalog_endpoints_hide_inactive_boxes (fulfillment.tests.test_http.WarehouseHttpTests.test_catalog_endpoints_hide_inactive_boxes) ... ok
test_page_lists_products_and_hides_inactive_boxes (fulfillment.tests.test_http.WarehouseHttpTests.test_page_lists_products_and_hides_inactive_boxes) ... ok
test_phone_form_recommends_the_mailer_without_saving (fulfillment.tests.test_http.WarehouseHttpTests.test_phone_form_recommends_the_mailer_without_saving) ... ok
test_saving_the_form_stores_the_order (fulfillment.tests.test_http.WarehouseHttpTests.test_saving_the_form_stores_the_order) ... ok
test_a_tiny_search_budget_does_not_invent_a_fit (fulfillment.tests.test_packing.PackingTests.test_a_tiny_search_budget_does_not_invent_a_fit) ... ok
test_exact_fill (fulfillment.tests.test_packing.PackingTests.test_exact_fill) ... ok
test_four_cubes_that_clear_the_volume_check_still_do_not_pack (fulfillment.tests.test_packing.PackingTests.test_four_cubes_that_clear_the_volume_check_still_do_not_pack) ... ok
test_greedy_commits_to_a_blocking_orientation_and_search_recovers (fulfillment.tests.test_packing.PackingTests.test_greedy_commits_to_a_blocking_orientation_and_search_recovers) ... ok
test_item_that_is_too_long_in_every_orientation_is_rejected (fulfillment.tests.test_packing.PackingTests.test_item_that_is_too_long_in_every_orientation_is_rejected) ... ok
test_items_stack_on_the_axis_that_has_room (fulfillment.tests.test_packing.PackingTests.test_items_stack_on_the_axis_that_has_room) ... ok
test_more_than_eight_items_are_not_called_impossible_when_search_is_skipped (fulfillment.tests.test_packing.PackingTests.test_more_than_eight_items_are_not_called_impossible_when_search_is_skipped) ... ok
test_nine_small_cubes_are_confirmed_by_the_greedy_placer (fulfillment.tests.test_packing.PackingTests.test_nine_small_cubes_are_confirmed_by_the_greedy_placer) ... ok
test_rotation_is_used_when_the_stored_orientation_does_not_fit (fulfillment.tests.test_packing.PackingTests.test_rotation_is_used_when_the_stored_orientation_does_not_fit) ... ok
test_same_request_returns_the_same_placement (fulfillment.tests.test_packing.PackingTests.test_same_request_returns_the_same_placement) ... ok
test_search_proves_two_large_cubes_do_not_fit_within_a_small_budget (fulfillment.tests.test_packing.PackingTests.test_search_proves_two_large_cubes_do_not_fit_within_a_small_budget) ... ok
test_touching_faces_are_allowed (fulfillment.tests.test_packing.PackingTests.test_touching_faces_are_allowed) ... ok
test_volume_rejects_before_a_search (fulfillment.tests.test_packing.PackingTests.test_volume_rejects_before_a_search) ... ok
test_a_heavier_box_is_used_when_the_cheap_box_cannot_carry_the_weight (fulfillment.tests.test_selector.SelectorTests.test_a_heavier_box_is_used_when_the_cheap_box_cannot_carry_the_weight) ... ok
test_an_unpackable_cheap_box_loses_to_a_larger_expensive_box (fulfillment.tests.test_selector.SelectorTests.test_an_unpackable_cheap_box_loses_to_a_larger_expensive_box) ... ok
test_empty_order_is_rejected (fulfillment.tests.test_selector.SelectorTests.test_empty_order_is_rejected) ... ok
test_equal_cost_and_volume_prefers_the_lower_id (fulfillment.tests.test_selector.SelectorTests.test_equal_cost_and_volume_prefers_the_lower_id) ... ok
test_equal_cost_prefers_the_smaller_volume (fulfillment.tests.test_selector.SelectorTests.test_equal_cost_prefers_the_smaller_volume) ... ok
test_float_dimensions_are_rejected (fulfillment.tests.test_selector.SelectorTests.test_float_dimensions_are_rejected) ... ok
test_low_budget_does_not_recommend_an_unproven_box (fulfillment.tests.test_selector.SelectorTests.test_low_budget_does_not_recommend_an_unproven_box) ... ok
test_lower_cost_beats_a_smaller_box (fulfillment.tests.test_selector.SelectorTests.test_lower_cost_beats_a_smaller_box) ... ok
test_no_boxes_is_explained (fulfillment.tests.test_selector.SelectorTests.test_no_boxes_is_explained) ... ok
test_rotation_survives_the_centimeter_conversion (fulfillment.tests.test_selector.SelectorTests.test_rotation_survives_the_centimeter_conversion) ... ok
test_size_is_reported_when_the_item_is_also_too_heavy (fulfillment.tests.test_selector.SelectorTests.test_size_is_reported_when_the_item_is_also_too_heavy) ... ok
test_volume_is_reported_when_the_order_is_also_too_heavy (fulfillment.tests.test_selector.SelectorTests.test_volume_is_reported_when_the_order_is_also_too_heavy) ... ok
test_weight_at_the_limit_fits_and_one_gram_over_does_not (fulfillment.tests.test_selector.SelectorTests.test_weight_at_the_limit_fits_and_one_gram_over_does_not) ... ok

----------------------------------------------------------------------
Ran 42 tests in 0.335s

OK
Destroying test database for alias 'default' ('file:memorydb_default?mode=memory&cache=shared')...

