import os
import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def draw_page_decorations(canvas, doc):
    canvas.saveState()
    
    # Primary brand color (Navy Blue)
    primary_color = colors.HexColor("#1a365d")
    border_color = colors.HexColor("#e2e8f0")
    text_muted = colors.HexColor("#4a5568")
    
    # Top header line & text
    canvas.setStrokeColor(primary_color)
    canvas.setLineWidth(1.5)
    canvas.line(54, 742, 558, 742)
    
    canvas.setFont("Helvetica-Bold", 8.5)
    canvas.setFillColor(primary_color)
    canvas.drawString(54, 750, "NEUROSCAN")
    
    canvas.setFont("Helvetica", 8.5)
    canvas.setFillColor(text_muted)
    canvas.drawString(120, 750, "|   FACE SCAN REPORT FOR STROKE DETECTION")
    
    # Bottom footer line & text
    canvas.setStrokeColor(border_color)
    canvas.setLineWidth(1)
    canvas.line(54, 50, 558, 50)
    
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(text_muted)
    canvas.drawString(54, 38, "NeuroScan is a screening tool, not a medical diagnosis. Always consult a clinician.")
    canvas.drawRightString(558, 38, f"Page {doc.page} of 2")
    
    canvas.restoreState()

def create_image_placeholder(label_text, width, height):
    """
    Creates a clean vector card placeholder if an image is missing,
    ensuring the report maintains a high-quality visual style without failing.
    """
    placeholder_style = ParagraphStyle(
        'PlaceholderStyle',
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#4a5568"),
        alignment=1 # Center
    )
    desc_style = ParagraphStyle(
        'PlaceholderDesc',
        fontName='Helvetica-Oblique',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#718096"),
        alignment=1 # Center
    )
    
    content = [
        Spacer(1, height / 2 - 22),
        Paragraph(label_text, placeholder_style),
        Spacer(1, 6),
        Paragraph("Visual element not loaded — showing layout template placeholder", desc_style)
    ]
    
    placeholder_table = Table([[content]], colWidths=[width], rowHeights=[height])
    placeholder_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f7fafc")),
        ('BOX', (0,0), (-1,-1), 1.5, colors.HexColor("#cbd5e0")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    return placeholder_table

def validate_inputs(features, prediction):
    """
    Validates types, structures, and keys of features and prediction dictionaries.
    Clipped to logical boundaries [0.0, 1.0] for features and [0.0, 100.0] for percentage.
    """
    if not isinstance(features, dict):
        raise TypeError(f"features must be a dictionary, got {type(features).__name__}")
    if not isinstance(prediction, dict):
        raise TypeError(f"prediction must be a dictionary, got {type(prediction).__name__}")
        
    required_features = [
        'eye_asymmetry', 'mouth_corner_drop', 'eyebrow_height_diff',
        'nasolabial_asymmetry', 'face_midline_deviation', 'mouth_width_asymmetry'
    ]
    
    validated_features = {}
    for k in required_features:
        if k not in features:
            raise KeyError(f"Missing required clinical feature key: '{k}'")
        val = features[k]
        if not isinstance(val, (int, float)):
            try:
                val = float(val)
            except (ValueError, TypeError):
                raise ValueError(f"Feature value for '{k}' must be a number, got {type(val).__name__}")
        validated_features[k] = max(0.0, min(1.0, float(val)))
        
    if 'percentage' not in prediction:
        raise KeyError("prediction dictionary must contain 'percentage' key")
    pct = prediction['percentage']
    if not isinstance(pct, (int, float)):
        try:
            pct = float(pct)
        except (ValueError, TypeError):
            raise ValueError(f"prediction['percentage'] must be a number, got {type(pct).__name__}")
    
    validated_prediction = {
        'percentage': max(0.0, min(100.0, float(pct))),
        'risk_level': str(prediction.get('risk_level', 'UNKNOWN RISK')),
        'color_hint': str(prediction.get('color_hint', 'green')).lower()
    }
    
    if validated_prediction['color_hint'] not in ['green', 'orange', 'red']:
        validated_prediction['color_hint'] = 'green'
        
    return validated_features, validated_prediction

def generate_pdf_report(features, prediction, annotated_img_path=None, gauge_img_path=None, output_pdf_path=None, pagesize_name="letter"):
    """
    Generates a premium 2-page PDF report.
    - Page 1: Title, Scan Details, Risk Level Card, and Annotated Face Mesh Image
    - Page 2: Detailed Asymmetry Table (with Clinical references), Gauge Chart, Clinical Recommendations & Disclaimers
    """
    try:
        # 1. Input Validation
        features, prediction = validate_inputs(features, prediction)
        
        # 2. Dynamic Output Path (generic path for home directory if output_pdf_path is None)
        if output_pdf_path is None:
            home_dir = os.path.expanduser("~")
            documents_dir = os.path.join(home_dir, "Documents")
            os.makedirs(documents_dir, exist_ok=True)
            today_str = datetime.date.today().strftime("%Y-%m-%d")
            output_pdf_path = os.path.join(documents_dir, f"NeuroScan-Report-{today_str}.pdf")
            
        # 3. Dynamic Page Size Support
        pagesizes = {"letter": letter, "a4": A4}
        pagesize = pagesizes.get(pagesize_name.lower(), letter)
        
        # Initialize Document
        doc = SimpleDocTemplate(
            output_pdf_path,
            pagesize=pagesize,
            leftMargin=54,
            rightMargin=54,
            topMargin=72,
            bottomMargin=72
        )
        
        styles = getSampleStyleSheet()
        
        # Typography styling
        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=26,
            leading=30,
            textColor=colors.HexColor("#1a365d"),
            spaceAfter=4
        )
        
        subtitle_style = ParagraphStyle(
            'ReportSubtitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=11,
            leading=15,
            textColor=colors.HexColor("#2d3748"),
            spaceAfter=15
        )
        
        section_heading = ParagraphStyle(
            'SectionHeading',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=14.5,
            leading=18,
            textColor=colors.HexColor("#1a365d"),
            spaceBefore=10,
            spaceAfter=8,
            keepWithNext=True
        )
        
        body_style = ParagraphStyle(
            'ReportBody',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=14.5,
            textColor=colors.HexColor("#1a202c")
        )
        
        meta_label_style = ParagraphStyle(
            'MetaLabel',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9.5,
            leading=13,
            textColor=colors.HexColor("#2d3748")
        )
        
        meta_val_style = ParagraphStyle(
            'MetaVal',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9.5,
            leading=13,
            textColor=colors.HexColor("#1a202c")
        )
        
        disclaimer_style = ParagraphStyle(
            'DisclaimerText',
            parent=styles['Normal'],
            fontName='Helvetica-Oblique',
            fontSize=8.5,
            leading=12,
            textColor=colors.HexColor("#4a5568")
        )
        
        story = []
        
        # ------------------ PAGE 1 ------------------
        # Header text
        story.append(Paragraph("Face Scan Report", title_style))
        story.append(Paragraph("Stroke Detection Screening Analysis by NeuroScan", subtitle_style))
        
        # Score card and risk themes
        risk_pct = prediction['percentage']
        risk_level = prediction['risk_level']
        color_hint = prediction['color_hint']
        
        if color_hint == 'red':
            theme_color = colors.HexColor("#e53e3e")      # Red
            bg_color = colors.HexColor("#fff5f5")         # Light red
            risk_text = "HIGH RISK — Seek immediate medical help"
        elif color_hint == 'orange':
            theme_color = colors.HexColor("#dd6b20")     # Orange
            bg_color = colors.HexColor("#fffaf0")         # Light orange
            risk_text = "MODERATE RISK — Consult a doctor"
        else:
            theme_color = colors.HexColor("#38a169")      # Green
            bg_color = colors.HexColor("#f0fff4")         # Light green
            risk_text = "LOW RISK"
            
        # Metadata left table
        scan_date = datetime.datetime.now().strftime("%B %d, %Y")
        scan_time = datetime.datetime.now().strftime("%I:%M %p")
        
        meta_data = [
            [Paragraph("Scan ID:", meta_label_style), Paragraph(f"NS-{datetime.datetime.now().strftime('%Y%m%d%H%M')}", meta_val_style)],
            [Paragraph("Scan Date:", meta_label_style), Paragraph(scan_date, meta_val_style)],
            [Paragraph("Scan Time:", meta_label_style), Paragraph(scan_time, meta_val_style)],
            [Paragraph("Methodology:", meta_label_style), Paragraph("MediaPipe Face Mesh + ML Classifier", meta_val_style)]
        ]
        
        meta_table = Table(meta_data, colWidths=[80, 190])
        meta_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ]))
        
        # Score card right block (enforced text wrapping, no overflow)
        score_label_style = ParagraphStyle(
            'ScoreLabel',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9.5,
            leading=13,
            textColor=colors.HexColor("#4a5568"),
            alignment=1
        )
        score_val_style = ParagraphStyle(
            'ScoreVal',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=26,
            leading=30,
            textColor=theme_color,
            alignment=1
        )
        risk_label_style = ParagraphStyle(
            'RiskLabel',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=10.5,
            leading=14.5,
            textColor=theme_color,
            alignment=1
        )
        
        score_card_data = [
            [Paragraph("OVERALL ASYMMETRY SCORE", score_label_style)],
            [Spacer(1, 4)],
            [Paragraph(f"{risk_pct:.1f}%", score_val_style)],
            [Spacer(1, 4)],
            [Paragraph(risk_text.upper(), risk_label_style)]
        ]
        
        score_card_table = Table(score_card_data, colWidths=[204])
        score_card_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), bg_color),
            ('BOX', (0,0), (-1,-1), 1.5, theme_color),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 10),
            ('BOTTOMPADDING', (0,0), (-1,-1), 10),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
            ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ]))
        
        layout_data = [[meta_table, score_card_table]]
        layout_table = Table(layout_data, colWidths=[280, 224])
        layout_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ]))
        
        story.append(layout_table)
        story.append(Spacer(1, 15))
        
        story.append(Paragraph("Visual Facial Mesh Examination", section_heading))
        story.append(Paragraph(
            "Below is the client's photograph annotated with the MediaPipe 468-point Face Mesh. "
            "The system has highlighted landmarks where facial asymmetry was analyzed. "
            "Green circles indicate symmetric regions within normal boundaries, while red circles mark "
            "landmarks that exceed clinical asymmetry thresholds.",
            body_style
        ))
        story.append(Spacer(1, 12))
        
        # Face Mesh Photo Block (Image Aspect Ratio preserved programmatically or clean vector placeholder)
        if annotated_img_path and os.path.exists(annotated_img_path):
            from PIL import Image as PILImage
            try:
                img_w, img_h = PILImage.open(annotated_img_path).size
                aspect = img_w / img_h
                display_h = 240
                display_w = display_h * aspect
                
                face_img = Image(annotated_img_path, width=display_w, height=display_h)
                face_img.hAlign = 'CENTER'
                story.append(face_img)
            except Exception:
                # Safe image loading fallback
                face_img = Image(annotated_img_path, width=198, height=240)
                face_img.hAlign = 'CENTER'
                story.append(face_img)
        else:
            # High-quality vector placeholder card if image is missing
            placeholder = create_image_placeholder("FACE PHOTO / MESH EXAMINATION VIEW", 360, 240)
            story.append(placeholder)
            
        story.append(PageBreak())
        
        # ------------------ PAGE 2 ------------------
        story.append(Paragraph("Detailed Asymmetry Breakdown", section_heading))
        story.append(Paragraph(
            "The table below details the 6 key facial asymmetry metrics extracted by MediaPipe landmarks. "
            "Each score represents the normalized difference between the left and right sides of the face (0 to 1 scale). "
            "A feature is flagged as <b>HIGH</b> if its measured value exceeds the clinically established threshold.",
            body_style
        ))
        story.append(Spacer(1, 10))
        
        # Table Styling
        table_header_style = ParagraphStyle(
            'TableHeader',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9,
            leading=12,
            textColor=colors.white
        )
        
        table_cell_style = ParagraphStyle(
            'TableCell',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8.5,
            leading=12.5,
            textColor=colors.HexColor("#1a202c")
        )
        
        table_cell_bold = ParagraphStyle(
            'TableCellBold',
            parent=table_cell_style,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor("#1a365d")
        )
        
        table_cell_normal_status = ParagraphStyle(
            'TableStatusNormal',
            parent=table_cell_style,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor("#38a169")
        )
        
        table_cell_high_status = ParagraphStyle(
            'TableStatusHigh',
            parent=table_cell_style,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor("#e53e3e")
        )
        
        FEATURE_NAMES = {
            'eye_asymmetry': 'Eye Asymmetry (Ptosis)',
            'mouth_corner_drop': 'Mouth Corner Droop',
            'eyebrow_height_diff': 'Eyebrow Height Difference',
            'nasolabial_asymmetry': 'Nasolabial Fold Asymmetry',
            'face_midline_deviation': 'Facial Midline Deviation',
            'mouth_width_asymmetry': 'Mouth Width Asymmetry'
        }
        
        THRESHOLDS = {
            'eye_asymmetry': 0.12, 'mouth_corner_drop': 0.10,
            'eyebrow_height_diff': 0.08, 'nasolabial_asymmetry': 0.10,
            'face_midline_deviation': 0.05, 'mouth_width_asymmetry': 0.10,
        }
        
        # Reference clinical bases
        FEATURE_BASES = {
            'eye_asymmetry': 'Ross et al. (Sunnybrook FGS)',
            'mouth_corner_drop': 'Kothari et al. (CPSS FAST)',
            'eyebrow_height_diff': 'Ross et al. (Sunnybrook FGS)',
            'nasolabial_asymmetry': 'Taufique & Savakis (2021)',
            'face_midline_deviation': 'Taufique & Savakis (2021)',
            'mouth_width_asymmetry': 'Kothari et al. (CPSS FAST)'
        }
        
        table_data = [
            [
                Paragraph("Facial Feature Metric", table_header_style),
                Paragraph("Measured Value", table_header_style),
                Paragraph("Normal Threshold", table_header_style),
                Paragraph("Clinical Basis / Reference", table_header_style),
                Paragraph("Symmetry Status", table_header_style)
            ]
        ]
        
        for key, display_name in FEATURE_NAMES.items():
            val = features[key]
            thresh = THRESHOLDS[key]
            basis = FEATURE_BASES[key]
            is_high = val > thresh
            
            status_text = "✗ HIGH" if is_high else "✓ Normal"
            status_style = table_cell_high_status if is_high else table_cell_normal_status
            
            table_data.append([
                Paragraph(display_name, table_cell_bold),
                Paragraph(f"{val:.3f}", table_cell_style),
                Paragraph(f"&le; {thresh:.2f}", table_cell_style),
                Paragraph(basis, table_cell_style),
                Paragraph(status_text, status_style)
            ])
            
        # Total width: 504 points (164 + 80 + 85 + 105 + 70 = 504)
        feat_table = Table(table_data, colWidths=[164, 80, 85, 105, 70])
        feat_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1a365d")),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e0")),
            ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#f7fafc")),
            ('BACKGROUND', (0,2), (-1,2), colors.white),
            ('BACKGROUND', (0,3), (-1,3), colors.HexColor("#f7fafc")),
            ('BACKGROUND', (0,4), (-1,4), colors.white),
            ('BACKGROUND', (0,5), (-1,5), colors.HexColor("#f7fafc")),
            ('BACKGROUND', (0,6), (-1,6), colors.white),
        ]))
        
        story.append(feat_table)
        story.append(Spacer(1, 12))
        
        # Recommendations & Calibration block
        story.append(Paragraph("Risk Level Calibration", section_heading))
        
        rec_text = ""
        if color_hint == 'red':
            rec_text = (
                "<b>CRITICAL FINDING:</b> Significant facial asymmetry has been detected in key facial regions, "
                "exceeding established clinical thresholds. In accordance with the FAST protocol, this is a strong indicator "
                "of potential acute stroke or facial nerve palsy.<br/><br/>"
                "<b>RECOMMENDED ACTION:</b> Please seek emergency medical help immediately. Call emergency services "
                "<b>(999 or 911)</b> or go to the nearest emergency department without delay. "
                "Do not wait to see if symptoms improve."
            )
        elif color_hint == 'orange':
            rec_text = (
                "<b>MODERATE FINDING:</b> Mild to moderate facial asymmetry is observed, with one or more metrics "
                "registering slightly above normal thresholds. This may indicate early-stage, minor, or transient facial "
                "asymmetry.<br/><br/>"
                "<b>RECOMMENDED ACTION:</b> We recommend consulting a healthcare provider or physician for a comprehensive "
                "clinical evaluation. If you experience other neurological signs (e.g., arm weakness, speech difficulty, "
                "numbness, or confusion), seek emergency medical care <b>(999 or 911)</b> immediately."
            )
        else:
            rec_text = (
                "<b>NORMAL FINDING:</b> All measured facial symmetry features are well within normal clinical limits. "
                "No significant facial drooping, brow asymmetry, or nasolabial discrepancy was detected.<br/><br/>"
                "<b>RECOMMENDED ACTION:</b> Continue routine health monitoring. While the facial scan is normal, please note "
                "that not all strokes present with facial drooping. If you or someone else experience sudden weakness in "
                "the arms/legs, slurred speech, sudden confusion, or severe headache, contact emergency services <b>(999 or 911)</b> immediately."
            )
            
        rec_paragraph = Paragraph(rec_text, ParagraphStyle('RecText', parent=body_style, fontSize=9, leading=13))
        
        # Render Gauge Chart preservation or clean placeholder
        if gauge_img_path and os.path.exists(gauge_img_path):
            from PIL import Image as PILImage
            try:
                g_w, g_h = PILImage.open(gauge_img_path).size
                g_aspect = g_w / g_h
                display_gw = 200
                display_gh = display_gw / g_aspect
                gauge_img = Image(gauge_img_path, width=display_gw, height=display_gh)
            except Exception:
                gauge_img = Image(gauge_img_path, width=200, height=128)
        else:
            gauge_img = create_image_placeholder("CALIBRATION GAUGE CHART", 200, 128)
            
        col_table = Table([[gauge_img, rec_paragraph]], colWidths=[210, 294])
        col_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (0,0), 0),
            ('RIGHTPADDING', (0,0), (0,0), 10),
            ('LEFTPADDING', (1,0), (1,0), 10),
            ('RIGHTPADDING', (1,0), (1,0), 0),
            ('TOPPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ]))
        story.append(col_table)
        story.append(Spacer(1, 12))
        
        # Clinical References block
        story.append(Paragraph("Clinical References", ParagraphStyle('RefHeading', parent=section_heading, fontSize=10.5, spaceBefore=2, spaceAfter=2)))
        ref_text = (
            "1. Herpich et al. Human vs. Machine Learning Based Detection of Facial Weakness Using Video Analysis. <i>Front. Neurol.</i>, 2022.<br/>"
            "2. Taufique, A. & Savakis, A. Automatic Quantification of Facial Asymmetry Using Facial Landmarks. <i>arXiv:2103.11059</i>, 2021.<br/>"
            "3. Kothari et al. Cincinnati Prehospital Stroke Scale: reproducibility and validity. <i>Acad. Emerg. Med.</i>, 1999."
        )
        story.append(Paragraph(ref_text, ParagraphStyle('RefText', parent=body_style, fontSize=7.5, leading=10, textColor=colors.HexColor("#4a5568"))))
        story.append(Spacer(1, 10))
        
        # Disclaimer rendered at full width (504 points) without QR code
        disclaimer_para = Paragraph(
            "<b>Medical Disclaimer:</b> This report is generated automatically by an artificial intelligence screening tool. "
            "It is designed solely for screening purposes to identify potential facial asymmetry. This report does NOT constitute "
            "medical advice, a diagnosis, or a treatment plan. A negative scan does not guarantee the absence of a stroke, and a "
            "positive scan does not guarantee the presence of a stroke. Always consult with a licensed healthcare professional for "
            "any clinical evaluation or diagnosis.",
            disclaimer_style
        )
        story.append(disclaimer_para)
        
        # Build Document
        doc.build(story, onFirstPage=draw_page_decorations, onLaterPages=draw_page_decorations)
        print(f"✅ PDF successfully generated at: {output_pdf_path}")
        return True
        
    except Exception as e:
        import traceback
        print(f"❌ Error occurred during PDF generation: {e}")
        traceback.print_exc()
        return False
