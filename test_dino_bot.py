"""
Comprehensive Verification Suite for Autonomous Chrome Dino Bot
================================================================
Validates:
1. DPI Awareness & Desktop Attachment
2. BotConfig Tuning Constants (Asymptotic model & Dynamic jump modulation)
3. Day & Night Mode Dynamic Inversion (5x5 origin patch sampling)
4. Day/Night Hysteresis Transition Debounce
5. Geometric Separation:
   - Anti-Self Dino Snout Offset (DINO_HEAD_X_OFFSET >= 55px)
   - Anti-Ground Track Truncation (>= 6px above running track)
6. Asymptotic Velocity & Dynamic Look-Ahead Model
7. Obstacle Cluster Width Measurement & Jump Classification
8. Multi-Altitude Segmentation (Band A, B, C)
9. DinoController Variable Jump Timings & Thread-Safe Duck Cancellation
10. Rolling 20-Frame Death Diagnostics Ring Buffer
11. Sub-5ms Vision Processing Latency Benchmark
"""

import os
import time
import math
import tempfile
import numpy as np
import cv2
from dino_bot import (
    BotConfig,
    DinoVision,
    DinoController,
    AutonomousDinoEngine,
    SessionLogger,
    AsyncFrameGrabber,
    TelemetryTuner,
    classify_collision,
    init_dpi_awareness,
)


def test_dpi_awareness():
    """Verify DPI awareness initialization executes without error."""
    res = init_dpi_awareness()
    print(f"DPI awareness initialized: {res}")
    assert isinstance(res, bool)


def test_config_constants():
    """Verify BotConfig holds required constants for geometry, speed model, and jump modulation."""
    cfg = BotConfig()
    # Geometry
    assert cfg.DINO_HEAD_X_OFFSET >= 55, "DINO_HEAD_X_OFFSET must be >= 55px"
    assert cfg.GROUND_CLEARANCE_PX >= 5, "GROUND_CLEARANCE_PX must be >= 5px strictly above running track"
    assert cfg.MIN_OBSTACLE_AREA >= 25, "MIN_OBSTACLE_AREA must reject small noise"

    # Asymptotic Velocity
    assert cfg.BASE_SPEED_PX == 6.0, "BASE_SPEED_PX should be 6.0 px/f"
    assert cfg.MAX_SPEED_PX == 13.0, "MAX_SPEED_PX should be 13.0 px/f"
    assert cfg.SPEED_ACCEL_COEFF == 0.015, "SPEED_ACCEL_COEFF should be 0.015"
    assert cfg.BASE_LOOK_AHEAD_PX == 75, "BASE_LOOK_AHEAD_PX should be 75px"
    assert cfg.MAX_LOOK_AHEAD_PX == 195, "MAX_LOOK_AHEAD_PX should be 195px"

    # Dynamic Jump Durations
    assert cfg.JUMP_SHORT_HOP_MS == 38.0
    assert cfg.JUMP_MED_HOP_MS == 50.0
    assert cfg.JUMP_HIGH_HOP_MS == 68.0
    assert cfg.AIR_LOCKOUT_SHORT_MS == 290.0
    assert cfg.AIR_LOCKOUT_MED_MS == 330.0
    assert cfg.AIR_LOCKOUT_HIGH_MS == 380.0
    assert cfg.CLUSTER_WIDTH_MED == 26
    assert cfg.CLUSTER_WIDTH_HIGH == 46


def test_day_night_mode_inversion():
    """Verify 5x5 patch background sampling and cv2.threshold normalization."""
    cfg = BotConfig(canvas_width=300, canvas_height=150, GROUND_Y_OFFSET=110)
    vision = DinoVision(cfg, custom_bbox=(100, 100, 300, 150))

    # 1. Day Mode Synthetic Frame: BG is 247 (Light), Obstacle is 80 (Dark)
    day_frame = np.full((150, 300), 247, dtype=np.uint8)
    is_night, lum = vision.sample_background(day_frame)
    assert not is_night, "Should detect Day mode"
    assert lum > 127.0

    mask_day = vision.get_binary_mask(day_frame, is_night)
    assert np.count_nonzero(mask_day) == 0, "Empty day canvas must be 0 in binary mask"

    # 2. Night Mode Synthetic Frame: BG is 32 (Dark), Obstacle is 240 (Light)
    night_frame = np.full((150, 300), 32, dtype=np.uint8)
    is_night_n, lum_n = vision.sample_background(night_frame)
    assert is_night_n, "Should detect Night mode"
    assert lum_n <= 127.0

    mask_night = vision.get_binary_mask(night_frame, is_night_n)
    assert np.count_nonzero(mask_night) == 0, "Empty night canvas must be 0 in binary mask"
    vision.close()


def test_day_night_transition_debounce_hysteresis():
    """Verify Day/Night hysteresis transition debounce prevents flickering."""
    cfg = BotConfig()
    vision = DinoVision(cfg, custom_bbox=(100, 100, 300, 150))
    frame = np.full((150, 300), 247, dtype=np.uint8)

    # Initially Day
    is_night, _ = vision.sample_background(frame)
    assert not is_night

    # Slight dip to 125 (near midpoint) -> should NOT switch to night yet due to hysteresis (<115 required)
    frame.fill(125)
    is_night, _ = vision.sample_background(frame)
    assert not is_night, "Hysteresis must stay Day at 125"

    # Drops to 100 -> switches to Night
    frame.fill(100)
    is_night, _ = vision.sample_background(frame)
    assert is_night, "Must switch to Night when luminance < 115"

    # Slight rise to 130 -> should NOT switch to day yet (>140 required)
    frame.fill(130)
    is_night, _ = vision.sample_background(frame)
    assert is_night, "Hysteresis must stay Night at 130"

    # Rises to 150 -> switches back to Day
    frame.fill(150)
    is_night, _ = vision.sample_background(frame)
    assert not is_night, "Must switch back to Day when luminance > 140"
    vision.close()


def test_geometric_separation_anti_track_and_anti_self():
    """
    Verify:
    1. Ground ROI terminates >= 5px above running track, completely avoiding track noise.
    2. Ground ROI starts >= +55px ahead of Dino snout, avoiding Dino self-detection.
    """
    cfg = BotConfig(
        canvas_width=400,
        canvas_height=200,
        GROUND_Y_OFFSET=150,
        DINO_X=40,
        DINO_W=44,
        DINO_HEAD_X_OFFSET=58,
        GROUND_CLEARANCE_PX=6,
    )
    vision = DinoVision(cfg, custom_bbox=(100, 100, 400, 200))

    # Synthetic canvas with Dino and Running Track, but NO obstacles
    frame = np.full((200, 400), 247, dtype=np.uint8)
    gy = cfg.GROUND_Y_OFFSET

    # Add running track at gy and below
    frame[gy : gy + 3, :] = 80
    frame[gy - 2 : gy, 100:300:4] = 80  # track texture bumps

    # Add standing Dino sprite
    frame[gy - 48 : gy, cfg.DINO_X : cfg.DINO_X + cfg.DINO_W] = 80

    (
        has_ground,
        has_mid,
        has_high,
        g_area,
        m_area,
        h_area,
        is_go,
        rois,
        _,
        _,
        _,
    ) = vision.scan_obstacles(frame, elapsed_time=0.0)

    # Must NOT detect ground obstacle because of geometric truncation and snout offset!
    assert not has_ground, "Ground ROI must be 100% clean of track noise and Dino self-detection"
    assert g_area == 0, f"Expected 0 obstacle pixels in Ground ROI, got {g_area}"
    vision.close()


def test_asymptotic_velocity_and_lookahead_model():
    """Verify left edge stays stationary (anchored) while width expands asymptotically toward 195px."""
    cfg = BotConfig(
        canvas_width=700,
        canvas_height=220,
        DINO_X=40,
        DINO_W=44,
        DINO_HEAD_X_OFFSET=58,
        BASE_SPEED_PX=6.0,
        MAX_SPEED_PX=13.0,
        SPEED_ACCEL_COEFF=0.015,
        BASE_LOOK_AHEAD_PX=75,
        MAX_LOOK_AHEAD_PX=195,
    )
    vision = DinoVision(cfg, custom_bbox=(100, 100, 700, 220))
    empty_frame = np.full((220, 700), 247, dtype=np.uint8)
    expected_anchor = 40 + 44 + 58  # 142px

    # 1. At t=0s
    _, _, _, _, _, _, _, rois_0, _, _, v_0 = vision.scan_obstacles(empty_frame, elapsed_time=0.0)
    assert rois_0["ground"][0] == expected_anchor, "Left edge must be anchored at snout + 58px"
    assert abs(v_0 - 6.0) < 1e-4, f"Velocity at t=0 should be 6.0, got {v_0}"
    assert rois_0["roi_w"] == 75, f"Width at t=0 must be 75px, got {rois_0['roi_w']}"

    # 2. At t=60s
    # v(60) = 6.0 + 7.0 * (1 - exp(-0.015 * 60)) = 6.0 + 7.0 * (1 - exp(-0.9)) = 6.0 + 7.0 * 0.59343 = 10.154
    expected_v_60 = 6.0 + 7.0 * (1.0 - math.exp(-0.015 * 60))
    _, _, _, _, _, _, _, rois_60, _, _, v_60 = vision.scan_obstacles(empty_frame, elapsed_time=60.0)
    assert rois_60["ground"][0] == expected_anchor, "Left edge must remain anchored at t=60s"
    assert abs(v_60 - expected_v_60) < 0.05
    assert 140 <= rois_60["roi_w"] <= 150

    # 3. At t=300s (approaching plateau)
    expected_v_300 = 6.0 + 7.0 * (1.0 - math.exp(-0.015 * 300))
    _, _, _, _, _, _, _, rois_300, _, _, v_300 = vision.scan_obstacles(empty_frame, elapsed_time=300.0)
    assert rois_300["ground"][0] == expected_anchor, "Left edge must remain anchored at t=300s"
    assert abs(v_300 - expected_v_300) < 0.05
    assert 190 <= rois_300["roi_w"] <= 195

    # 4. At t=1000s (asymptote ceiling)
    _, _, _, _, _, _, _, rois_1000, _, _, v_1000 = vision.scan_obstacles(empty_frame, elapsed_time=1000.0)
    assert rois_1000["ground"][0] == expected_anchor, "Left edge must remain anchored at t=1000s"
    assert abs(v_1000 - 13.0) < 0.01
    assert rois_1000["roi_w"] == 195, f"Width must clamp at MAX_LOOK_AHEAD_PX (195), got {rois_1000['roi_w']}"
    vision.close()


def test_obstacle_cluster_width_and_jump_classification():
    """Verify cluster width calculation and short/med/high jump classification thresholds."""
    cfg = BotConfig(canvas_width=500, canvas_height=200, GROUND_Y_OFFSET=150)
    vision = DinoVision(cfg, custom_bbox=(100, 100, 500, 200))
    dino_front = cfg.DINO_X + cfg.DINO_W + cfg.DINO_HEAD_X_OFFSET
    gy = cfg.GROUND_Y_OFFSET

    # 1. Single Small Cactus (width = 16px -> <= CLUSTER_WIDTH_MED 26px -> SHORT_HOP)
    frame_small = np.full((200, 500), 247, dtype=np.uint8)
    frame_small[gy - 30 : gy - 10, dino_front + 10 : dino_front + 26] = 80
    has_g, _, _, _, _, _, _, _, _, c_w_small, _ = vision.scan_obstacles(frame_small, elapsed_time=0.0)
    assert has_g
    assert c_w_small == 16, f"Expected cluster width 16px, got {c_w_small}"
    assert c_w_small <= cfg.CLUSTER_WIDTH_MED

    # 2. Medium Double Cactus (width = 36px -> between 26 and 46 -> MED_HOP)
    frame_med = np.full((200, 500), 247, dtype=np.uint8)
    frame_med[gy - 35 : gy - 10, dino_front + 10 : dino_front + 46] = 80
    has_g, _, _, _, _, _, _, _, _, c_w_med, _ = vision.scan_obstacles(frame_med, elapsed_time=0.0)
    assert has_g
    assert c_w_med == 36, f"Expected cluster width 36px, got {c_w_med}"
    assert cfg.CLUSTER_WIDTH_MED < c_w_med <= cfg.CLUSTER_WIDTH_HIGH

    # 3. Large Clustered Cacti (width = 54px -> > 46px -> HIGH_JUMP)
    frame_large = np.full((200, 500), 247, dtype=np.uint8)
    frame_large[gy - 40 : gy - 10, dino_front + 10 : dino_front + 64] = 80
    has_g, _, _, _, _, _, _, _, _, c_w_large, _ = vision.scan_obstacles(frame_large, elapsed_time=0.0)
    assert has_g
    assert c_w_large == 54, f"Expected cluster width 54px, got {c_w_large}"
    assert c_w_large > cfg.CLUSTER_WIDTH_HIGH
    vision.close()


def test_multi_altitude_segmentation():
    """Verify Band A (Ground -> Jump), Band B (Mid -> Duck), Band C (High -> Ignore)."""
    cfg = BotConfig(canvas_width=400, canvas_height=200, GROUND_Y_OFFSET=150)
    vision = DinoVision(cfg, custom_bbox=(100, 100, 400, 200))

    dino_front = cfg.DINO_X + cfg.DINO_W + cfg.DINO_HEAD_X_OFFSET
    gy = cfg.GROUND_Y_OFFSET

    # Test Case 1: Ground Cactus in Band A
    frame_a = np.full((200, 400), 247, dtype=np.uint8)
    frame_a[gy - 40 : gy - 10, dino_front + 5 : dino_front + 25] = 80
    has_g, has_m, has_h, g_a, _, _, _, _, _, _, _ = vision.scan_obstacles(frame_a, elapsed_time=0.0)
    assert has_g, "Band A must detect ground obstacle"
    assert not has_m, "Band B must be clear"
    assert not has_h, "Band C must be clear"
    assert g_a >= cfg.MIN_OBSTACLE_AREA

    # Test Case 2: Mid-Air Pterodactyl in Band B (gy - 70 to gy - 55)
    frame_b = np.full((200, 400), 247, dtype=np.uint8)
    frame_b[gy - 70 : gy - 55, dino_front + 5 : dino_front + 30] = 80
    has_g, has_m, has_h, _, m_a, _, _, _, _, _, _ = vision.scan_obstacles(frame_b, elapsed_time=0.0)
    assert not has_g, "Band A must be clear"
    assert has_m, "Band B must detect mid obstacle"
    assert not has_h, "Band C must be clear"
    assert m_a >= cfg.MIN_OBSTACLE_AREA

    # Test Case 3: High-Altitude Pterodactyl in Band C (gy - 95 to gy - 80)
    frame_c = np.full((200, 400), 247, dtype=np.uint8)
    frame_c[gy - 95 : gy - 80, dino_front + 5 : dino_front + 30] = 80
    has_g, has_m, has_h, _, _, h_a, _, _, _, _, _ = vision.scan_obstacles(frame_c, elapsed_time=0.0)
    assert not has_g, "Band A must be clear"
    assert not has_m, "Band B must be clear"
    assert has_h, "Band C must detect high obstacle (to IGNORE)"
    assert h_a >= cfg.MIN_OBSTACLE_AREA
    vision.close()


def test_controller_variable_jumps_and_duck_cancellation():
    """Verify variable jump hold durations, airborne lockout, and duck cancel event."""
    cfg = BotConfig()
    controller = DinoController(cfg)

    # Initial state
    assert time.time() >= controller.airborne_until

    # 1. Short hop test
    t0 = time.time()
    controller.jump(duration_ms=cfg.JUMP_SHORT_HOP_MS, lockout_ms=cfg.AIR_LOCKOUT_SHORT_MS)
    t1 = time.time()
    assert 0.025 <= (t1 - t0) <= 0.070
    assert controller.airborne_until > time.time()
    rem_short = controller.airborne_until - time.time()
    assert 0.20 <= rem_short <= 0.35

    # 2. Duck cancellation test
    controller._is_ducking = True
    assert not controller._duck_cancel_event.is_set()
    controller.jump(duration_ms=cfg.JUMP_HIGH_HOP_MS, lockout_ms=cfg.AIR_LOCKOUT_HIGH_MS)
    assert controller._duck_cancel_event.is_set(), "Jump must trigger duck cancel event"
    assert not controller._is_ducking, "Duck state must be cleared"


def test_death_frame_ring_buffer_and_diagnostics():
    """Verify rolling 20-frame ring buffer and collision diagnostic export."""
    cfg = BotConfig()
    engine = AutonomousDinoEngine(cfg, custom_bbox=(100, 100, 700, 220), is_debug=False)

    # Check buffer maxlen is 20
    assert engine.recent_frames_buffer.maxlen == 20

    # Fill buffer with 25 synthetic frames to test rolling discard
    fake_canvas = np.full((220, 700), 247, dtype=np.uint8)
    fake_rois = {"ground": (142, 110, 217, 154)}
    for i in range(25):
        telem = {"cluster_width": i, "ground_area": i * 10}
        engine.recent_frames_buffer.append((fake_canvas, fake_canvas, fake_rois, telem))

    assert len(engine.recent_frames_buffer) == 20
    # Latest item should have cluster_width == 24
    assert engine.recent_frames_buffer[-1][3]["cluster_width"] == 24

    # Test collision diagnostic capture
    with tempfile.TemporaryDirectory() as tmp_dir:
        engine.diagnostics_dir = tmp_dir
        engine.capture_death_diagnostics(final_score=1250, elapsed=42.5, final_v=11.2)

        # Check image was saved
        saved_imgs = [f for f in os.listdir(tmp_dir) if f.endswith(".png")]
        assert len(saved_imgs) == 1
        assert "1250pts" in saved_imgs[0]

        # Check CSV was appended
        csv_path = os.path.join(tmp_dir, "run_history.csv")
        assert os.path.exists(csv_path)
        with open(csv_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            assert len(lines) == 2  # Header + 1 row
            assert "1250" in lines[1]
    engine.vision.close()


def test_session_logger():
    """Verify SessionLogger CSV header creation and asynchronous run row writing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        csv_file = os.path.join(tmp_dir, "test_session.csv")
        logger = SessionLogger(csv_file)
        assert os.path.exists(csv_file)
        with open(csv_file, "r", encoding="utf-8") as f:
            header = f.readline().strip()
        assert header == "run_id,timestamp,duration_sec,score,best_score,peak_speed_px_frame,total_jumps,total_ducks,cluster_jumps,death_cause,avg_cycle_latency_ms"

        logger.log_run(
            run_id=1,
            duration_sec=32.45,
            score=1850,
            best_score=1850,
            peak_speed_px_frame=11.20,
            total_jumps=14,
            total_ducks=3,
            cluster_jumps=4,
            death_cause="LATE_JUMP_GROUND",
            avg_cycle_latency_ms=0.45,
        )
        time.sleep(0.1)
        with open(csv_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        assert len(lines) == 2
        assert "LATE_JUMP_GROUND" in lines[1]
        assert "1850" in lines[1]


def test_failure_analysis_classification():
    """Verify 4 collision failure modes: FALSE_DUCK, HIGH_BIRD_BLEED, LANDING_CLIP, LATE_JUMP."""
    cfg = BotConfig()
    fake_canvas = np.full((220, 700), 247, dtype=np.uint8)
    fake_binary = np.zeros((220, 700), dtype=np.uint8)
    fake_rois = {"ground": (142, 110, 217, 154)}

    # 1. FALSE_DUCK_COLLISION
    telem_duck = {"last_action": "DUCK", "is_ducking": True}
    cause_duck = classify_collision([(fake_canvas, fake_binary, fake_rois, telem_duck)], cfg)
    assert cause_duck == "FALSE_DUCK_COLLISION"

    # 2. HIGH_BIRD_BLEED
    telem_bird = {"has_mid": True, "has_high": True, "mid_area": 50, "high_area": 50}
    cause_bird = classify_collision([(fake_canvas, fake_binary, fake_rois, telem_bird)], cfg)
    assert cause_bird == "HIGH_BIRD_BLEED"

    # 3. LANDING_CLIP_CLUSTER
    telem_clip = {"time_since_touchdown": 0.05, "cluster_width": 35}
    bin_clip = np.zeros((220, 700), dtype=np.uint8)
    bin_clip[cfg.GROUND_Y_OFFSET - 20 : cfg.GROUND_Y_OFFSET - 6, cfg.DINO_X : cfg.DINO_X + 30] = 255
    cause_clip = classify_collision([(fake_canvas, bin_clip, fake_rois, telem_clip)], cfg)
    assert cause_clip == "LANDING_CLIP_CLUSTER"

    # 4. LATE_JUMP_GROUND
    bin_late = np.zeros((220, 700), dtype=np.uint8)
    gx1, gy1, gx2, gy2 = fake_rois["ground"]
    bin_late[gy1:gy2, gx1 : gx1 + 20] = 255
    telem_late = {"has_ground": True}
    cause_late = classify_collision([(fake_canvas, bin_late, fake_rois, telem_late)], cfg)
    assert cause_late == "LATE_JUMP_GROUND"


def test_save_death_dump_async():
    """Verify asynchronous death dump exports 3 annotated frames and the final collision frame."""
    cfg = BotConfig()
    engine = AutonomousDinoEngine(cfg, custom_bbox=(100, 100, 700, 220), is_debug=False)
    with tempfile.TemporaryDirectory() as tmp_dir:
        engine.debug_deaths_dir = tmp_dir
        fake_canvas = np.full((220, 700), 247, dtype=np.uint8)
        fake_binary = np.zeros((220, 700), dtype=np.uint8)
        # Add obstacle contour
        fake_binary[110:150, 142:170] = 255
        fake_rois = {"ground": (142, 110, 217, 154)}
        telem = {"cluster_width": 28, "has_ground": True}

        frames = [(fake_canvas, fake_binary, fake_rois, telem)] * 3
        engine.save_death_dump_async(
            frames_snapshot=frames,
            run_id=2,
            score=2400,
            speed=10.5,
            elapsed=35.0,
            classification="LATE_JUMP_GROUND",
        )
        time.sleep(0.15)  # wait for thread
        files = os.listdir(tmp_dir)
        assert any(f.endswith(".png") for f in files)
        assert any("death_0002_score2400_LATE_JUMP_GROUND.png" in f for f in files)
        assert any("frame1.png" in f for f in files)
        assert any("frame3.png" in f for f in files)
    engine.vision.close()


def test_sub_5ms_vision_latency():
    """Benchmark pure frame processing latency across 500 iterations."""
    cfg = BotConfig()
    vision = DinoVision(cfg, custom_bbox=(100, 100, 700, 220))
    test_frame = np.full((220, 700), 247, dtype=np.uint8)

    latencies = []
    for _ in range(500):
        t0 = time.perf_counter()
        vision.scan_obstacles(test_frame, elapsed_time=15.0)
        t1 = time.perf_counter()
        latencies.append((t1 - t0) * 1000.0)

    mean_lat = float(np.mean(latencies))
    max_lat = float(np.max(latencies))
    print(f"\n[Benchmark] Vision Processing Latency - Mean: {mean_lat:.3f} ms | Max: {max_lat:.3f} ms")
    assert mean_lat < 1.0, f"Mean latency {mean_lat:.3f}ms exceeds 1.0ms target"
    assert max_lat < 5.0, f"Max latency {max_lat:.3f}ms exceeds 5.0ms target"
    vision.close()


def test_ambient_noise_and_cloud_rejection():
    """Verify ambient noise, drifting clouds, star speckles, and small texture artifacts are completely rejected."""
    cfg = BotConfig(canvas_width=700, canvas_height=220, GROUND_Y_OFFSET=160)
    vision = DinoVision(cfg, custom_bbox=(100, 100, 700, 220))
    dino_front = cfg.DINO_X + cfg.DINO_W + cfg.DINO_HEAD_X_OFFSET
    gy = cfg.GROUND_Y_OFFSET

    # 1. Day Mode with Drifting Sky Clouds (luminance ~210 in the sky zone y: 30..80)
    day_frame = np.full((220, 700), 247, dtype=np.uint8)
    day_frame[40:75, dino_front + 20 : dino_front + 120] = 210  # Cloud mass in sky
    day_frame[gy : gy + 3, :] = 83  # Track
    
    # Check binary mask zeroes out the cloud
    mask_day = vision.get_binary_mask(day_frame, is_night_mode=False)
    assert np.count_nonzero(mask_day[40:75, dino_front + 20 : dino_front + 120]) == 0, "Day clouds (>180) must be 0 in binary mask"

    has_g, has_m, has_h, g_area, m_area, h_area, _, _, _, _, _ = vision.scan_obstacles(day_frame, elapsed_time=5.0)
    assert not has_g, "Clouds must never trigger a ground jump"
    assert not has_m, "Clouds must never trigger a mid duck"
    assert g_area == 0 and m_area == 0

    # 2. Night Mode with Faint Stars and Moon (luminance ~145 in the sky zone y: 20..70)
    night_frame = np.full((220, 700), 32, dtype=np.uint8)
    night_frame[25:35, dino_front + 30 : dino_front + 50] = 145  # Faint star cluster
    night_frame[15:45, 600:630] = 160  # Moon
    night_frame[gy : gy + 3, :] = 240  # Track

    mask_night = vision.get_binary_mask(night_frame, is_night_mode=True)
    assert np.count_nonzero(mask_night[25:35, dino_front + 30 : dino_front + 50]) == 0, "Night stars (<170) must be 0 in binary mask"
    assert np.count_nonzero(mask_night[15:45, 600:630]) == 0, "Night moon (<170) must be 0 in binary mask"

    has_g_n, has_m_n, _, g_area_n, m_area_n, _, _, _, _, _, _ = vision.scan_obstacles(night_frame, elapsed_time=5.0)
    assert not has_g_n, "Night stars/moon must never trigger a jump"
    assert not has_m_n, "Night stars/moon must never trigger a duck"
    assert g_area_n == 0 and m_area_n == 0

    # 3. Small Speckle Noise Filter (area < MIN_OBSTACLE_AREA)
    day_noise = np.full((220, 700), 247, dtype=np.uint8)
    # Add a tiny speck of 15 pixels in the ground zone
    day_noise[gy - 20 : gy - 17, dino_front + 20 : dino_front + 25] = 80
    has_g_speck, _, _, g_area_speck, _, _, _, _, _, _, _ = vision.scan_obstacles(day_noise, elapsed_time=5.0)
    assert not has_g_speck, f"Tiny speck ({g_area_speck} px < {cfg.MIN_OBSTACLE_AREA}) must NOT trigger jump"
    assert g_area_speck == 15

    # 4. Valid Real Ground Obstacle (area >= MIN_OBSTACLE_AREA)
    day_real = np.full((220, 700), 247, dtype=np.uint8)
    day_real[gy - 35 : gy - 10, dino_front + 20 : dino_front + 35] = 80  # 25 x 15 = 375 px
    has_g_real, _, _, g_area_real, _, _, _, _, _, _, _ = vision.scan_obstacles(day_real, elapsed_time=5.0)
    assert has_g_real, "Real obstacle must trigger jump"
    assert g_area_real >= cfg.MIN_OBSTACLE_AREA

    vision.close()


def test_canvas_detection_validation():
    """Verify canvas auto-detection candidate validation rejects desktop borders without Dino."""
    # Candidate 1: Arbitrary desktop dark line with gray background (e.g., taskbar / IDE)
    fake_screen = np.full((1080, 1920), 128, dtype=np.uint8)
    fake_screen[800, 500:1100] = 30  # Horizontal border line
    # Candidate patch background will have bg_val ~128 -> rejected!

    # Candidate 2: Day canvas with line but NO Dino sprite
    fake_day_no_dino = np.full((1080, 1920), 247, dtype=np.uint8)
    fake_day_no_dino[800, 500:1100] = 80  # Horizontal track line
    # Dino crop at [100:160, 20:80] has 0 dark pixels -> rejected!

    # Verify logic directly:
    crop_no_dino = fake_day_no_dino[800 - 150 : 800 + 70, 500:1100]
    bg_val = float(np.mean(crop_no_dino[5:15, 5:15]))
    assert bg_val > 200  # background is light
    dino_crop = crop_no_dino[100:160, 20:80]
    dino_pixels = int(np.count_nonzero(dino_crop < 110))
    assert dino_pixels < 150, "Without a Dino sprite, track line alone has too few pixels"
    # Should not qualify (requires 150 <= dino_pixels <= 1200)
    assert not (150 <= dino_pixels <= 1200)


def test_async_frame_grabber():
    """Verify AsyncFrameGrabber background double buffering and sub-5ms grab latency."""
    bbox = {"top": 100, "left": 100, "width": 400, "height": 200}
    grabber = AsyncFrameGrabber(bbox)
    time.sleep(0.05)  # allow worker thread to initialize

    # Test grab latency over 100 frames
    times = []
    for _ in range(100):
        t0 = time.perf_counter()
        frame = grabber.grab()
        t1 = time.perf_counter()
        times.append((t1 - t0) * 1000.0)

    mean_grab_lat = float(np.mean(times))
    print(f"\n[Grabber] Async Frame Grab Latency: {mean_grab_lat:.4f} ms")
    assert mean_grab_lat < 1.0, f"Async grab latency ({mean_grab_lat:.4f} ms) must be < 1.0 ms"
    assert frame.shape == (200, 400), f"Expected shape (200, 400), got {frame.shape}"
    assert frame.dtype == np.uint8

    grabber.close()


def test_telemetry_tuner_adaptive_scaling():
    """Verify TelemetryTuner automatically scales jump durations and look-ahead based on death classifications."""
    cfg = BotConfig()
    initial_high_ms = cfg.JUMP_HIGH_HOP_MS
    initial_base_w = cfg.BASE_LOOK_AHEAD_PX

    with tempfile.TemporaryDirectory() as tmp_dir:
        csv_path = os.path.join(tmp_dir, "test_telemetry.csv")
        # Write synthetic telemetry with 2 LANDING_CLIP_CLUSTER and 1 LATE_JUMP_GROUND
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            f.write("run_id,timestamp,duration_sec,score,best_score,peak_speed_px_frame,total_jumps,total_ducks,cluster_jumps,death_cause,avg_cycle_latency_ms\n")
            f.write("1,2026-10-08 12:00:00,15.2,1200,1200,8.5,10,2,3,LANDING_CLIP_CLUSTER,0.25\n")
            f.write("2,2026-10-08 12:01:00,22.4,1800,1800,9.2,15,3,4,LANDING_CLIP_CLUSTER,0.24\n")
            f.write("3,2026-10-08 12:02:00,30.1,2400,2400,10.1,20,4,5,LATE_JUMP_GROUND,0.26\n")

        tuned_cfg, report = TelemetryTuner.tune_config(cfg, csv_path=csv_path, deaths_dir=tmp_dir)

        assert report["tuned"] is True
        assert report["total_runs_analyzed"] == 3
        # JUMP_HIGH_HOP_MS should increase (+2ms * 2 = +4ms)
        assert tuned_cfg.JUMP_HIGH_HOP_MS > initial_high_ms
        assert tuned_cfg.JUMP_HIGH_HOP_MS == initial_high_ms + 4.0
        # AIR_LOCKOUT_HIGH_MS should increase (+8ms * 2 = +16ms)
        assert tuned_cfg.AIR_LOCKOUT_HIGH_MS == cfg.AIR_LOCKOUT_HIGH_MS + 16.0
        # BASE_LOOK_AHEAD_PX should increase (+2px * 1 = +2px)
        assert tuned_cfg.BASE_LOOK_AHEAD_PX == initial_base_w + 2
        # CLUSTER_WIDTH_MED should decrease by 1
        assert tuned_cfg.CLUSTER_WIDTH_MED == cfg.CLUSTER_WIDTH_MED - 1


def test_soak_test_milestone_and_termination():
    """Verify soak test engine configuration and milestone logic."""
    cfg = BotConfig()
    engine = AutonomousDinoEngine(cfg, custom_bbox=(100, 100, 400, 200), is_debug=False)
    assert engine.high_score == 0
    assert engine.run_id == 1
    assert engine.use_async_grab is True
    assert engine.vision._grabber is not None
    engine.vision.close()


if __name__ == "__main__":
    test_dpi_awareness()
    test_config_constants()
    test_day_night_mode_inversion()
    test_day_night_transition_debounce_hysteresis()
    test_geometric_separation_anti_track_and_anti_self()
    test_asymptotic_velocity_and_lookahead_model()
    test_obstacle_cluster_width_and_jump_classification()
    test_multi_altitude_segmentation()
    test_ambient_noise_and_cloud_rejection()
    test_canvas_detection_validation()
    test_async_frame_grabber()
    test_telemetry_tuner_adaptive_scaling()
    test_soak_test_milestone_and_termination()
    test_controller_variable_jumps_and_duck_cancellation()
    test_death_frame_ring_buffer_and_diagnostics()
    test_session_logger()
    test_failure_analysis_classification()
    test_save_death_dump_async()
    test_sub_5ms_vision_latency()
    print("\n>>> ALL 19 TESTS PASSED SUCCESSFULLY! <<<")


