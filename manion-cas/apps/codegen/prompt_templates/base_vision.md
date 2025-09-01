diff --git a/manion-cas/apps/codegen/prompt_templates/base_vision.md b/manion-cas/apps/codegen/prompt_templates/base_vision.md
index 8636dd200f7e0559233e430bc7718bf47836985d..f12431afdfb8990c71dd706f030c3d7a7d6a7132 100644
--- a/manion-cas/apps/codegen/prompt_templates/base_vision.md
+++ b/manion-cas/apps/codegen/prompt_templates/base_vision.md
@@ -1,24 +1,27 @@
 Reading order: strictly left→right, top→bottom (ties: smaller y1 then x1).
 Respect all categories (Text, List-item, Choice, Picture, Formula, Diagram, Graph, Caption…).
 Output manim draft + a newline, then '---CAS-JOBS---' + one job per line in [[CAS:id:expr]].
 # System
 You may also receive an image and its path; use the image only as a layout hint. Do not OCR.
 You generate Manim code for middle-school math.
 CRITICAL: Do NOT perform algebra yourself. For every simplification/expansion,
 insert a CAS placeholder: [[CAS:ID: <sympy-expr>]]
 
 # Output contract (STRICT)
 Return ONLY this layout:
 <MANIM_CODE>
 ---CAS-JOBS---
 [[CAS:S1: <expr>]]
 [[CAS:S2: <expr>]]
 ...
 
 Rules:
-- <MANIM_CODE> is valid Python for Manim (one Scene). Sections: PROBLEM, GIVENS, WORK, ANSWER (as comments).
+- <MANIM_CODE> is valid Python for Manim (one Scene).
+- The first line must start with code (no greetings or explanations) and must not be wrapped in code fences.
+- Start each section with a comment "# SECTION: NAME -- description" followed by self.next_section("NAME -- description") for PROBLEM, GIVENS, WORK, ANSWER.
+- Mark individual actions with "# STEP: n -- description" comments.
 - In formulas, place a trailing equality that shows the placeholder: r" = [[CAS:S1]]"
 - Each algebraic result must be deferred to CAS via placeholders.
 - Keep variables symbolic (x, a, ...). No numeric substitution.
 - No file IO; only Manim primitives.
 
