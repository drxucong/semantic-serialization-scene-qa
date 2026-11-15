@echo off
REM ===========================================================================
REM CONFIRMATORY RE-RUN ON UNSEEN FRAMES -- so that v15 can lead the paper.
REM
REM The problem this fixes. v9 earned the paper's headline honestly: its
REM criterion was frozen before it ran. v15 did not -- it is the winner of a
REM seven-way comparison (v9..v15) on the 1366-question development bank, and
REM putting it in the headline against that same bank would be reporting a
REM selection as a confirmation.
REM
REM The fix. A new bank on CODa_sm frames that are at least 15 frames (1.5 s)
REM from EVERY development frame -- the development bank's own median spacing,
REM so a confirmatory frame is as far from any development frame as two
REM development frames are from each other. 1356 frames, all 21 sequences,
REM same generator, same visible-scope gate, same families, new seed.
REM
REM CRITERIA, frozen 2026-08-08 23:0x, before the bank exists and before any
REM arm runs. Scene-cluster paired bootstrap, B=20000, seed 0, clusters =
REM recording sequences. Run-noise floor +-.006 (7B) / +-.008 (3B).
REM
REM   A1  PRIMARY   v15 - pixel VLM at 7B: CI lower bound > 0 AND delta > +.006
REM   A2  PRIMARY   v15 - pixel VLM at 3B: CI lower bound > 0 AND delta > +.008
REM   A3  DECISION  v15 - v9 at both scales, floor applied. The paper leads
REM                 with v15 only if v15 is not WORSE than v9 above the floor
REM                 at either scale. If v15 loses above the floor at 7B or 3B,
REM                 the paper keeps v9 and v15 is reported as an ablation.
REM
REM Nothing here may move after the first arm returns. A criterion that is not
REM met is a result: if A1/A2 fail, the paper says the advantage did not
REM replicate on unseen frames, and that sentence gets written.
REM ===========================================================================
setlocal
set "PROJ=C:\Users\drxuc\Desktop\phd\publications\llm navigation\Conference\NIPS2026\lvcworld"
set "LOG=%USERPROFILE%\Downloads\diskscan\confirm.log"
set "MK=%PROJ%\outputs\markers"
set PYTHONUTF8=1
cd /d "%PROJ%"
set PYT=env\vlbase\Scripts\python.exe
if not exist "%PYT%" set PYT=env\lvcworld\Scripts\python.exe
set PY=env\lvcworld\Scripts\python.exe
set P10=outputs\phase10\coda
set QA=outputs\coda\qa_confirm.jsonl
set ST=outputs\coda\states_confirm_v9.json
if not exist "%MK%" mkdir "%MK%"
echo ==== CONFIRM START %date% %time% ==== >> "%LOG%"

REM ---- 1. generate the bank -------------------------------------------------
if exist "%QA%" goto perceive
echo [confirm] generating the held-out bank %time% >> "%LOG%"
%PYT% scripts\coda\make_confirm_qa.py --coda data\coda_sm\CODa_sm --image-root data/coda_sm/CODa_sm --dev-states outputs\coda\states_kf_v9.json --min-sep 15 --out-qa %QA% --out-states outputs\coda\states_confirm_gt.json --seed 20260809 >> "%LOG%" 2>&1
if not exist "%QA%" (echo [confirm] ABORT: no bank generated >> "%LOG%" & goto fin)

REM ---- 2. perceive those frames, shipped configuration (yolo-conf .25) ------
:perceive
if exist "%ST%" goto arms
echo [confirm] perceiving the held-out frames, yolo-conf 0.25 %time% >> "%LOG%"
%PYT% scripts\coda\perceive_list.py --sids outputs\coda\qa_confirm_sids.txt --data-root data/coda_sm/CODa_sm --yolo-conf 0.25 --out %ST% >> "%LOG%" 2>&1
if not exist "%ST%" (echo [confirm] ABORT: no perceived state >> "%LOG%" & goto fin)

REM ---- 3. six arms ---------------------------------------------------------
:arms
set N=0
for /f %%i in (outputs\coda\qa_confirm_n.txt) do set N=%%i
echo [confirm] bank size N=%N% >> "%LOG%"
if "%N%"=="0" (echo [confirm] ABORT: no bank size, refusing to run arms >> "%LOG%" & goto fin)
if exist "%MK%\cf_v15_7b.done" goto c2
echo [confirm] v15 7B %time% >> "%LOG%"
%PY% scripts\paper\run_serializer_v15.py --depth 5 --qa %QA% --states %ST% --model qwen2.5:7b --out %P10%\results_cf_v15_7b >> "%LOG%" 2>&1
%PY% scripts\audit\mark_if_complete.py "%P10%\results_cf_v15_7b\state_typed__clean__forced.jsonl" %N% "%MK%\cf_v15_7b.done" >> "%LOG%" 2>&1

:c2
if exist "%MK%\cf_v15_3b.done" goto c3
echo [confirm] v15 3B %time% >> "%LOG%"
%PY% scripts\paper\run_serializer_v15.py --depth 5 --qa %QA% --states %ST% --model qwen2.5:3b --out %P10%\results_cf_v15_3b >> "%LOG%" 2>&1
%PY% scripts\audit\mark_if_complete.py "%P10%\results_cf_v15_3b\state_typed__clean__forced.jsonl" %N% "%MK%\cf_v15_3b.done" >> "%LOG%" 2>&1

:c3
if exist "%MK%\cf_px_7b.done" goto c4
echo [confirm] pixel VLM 7B %time% >> "%LOG%"
%PY% scripts\pilot\run_pixel_retry.py --subset %QA% --dataroot . --model qwen2.5vl:7b --out %P10%\results_cf_px_7b >> "%LOG%" 2>&1
%PY% scripts\audit\mark_if_complete.py "%P10%\results_cf_px_7b\pixel__clean__forced.jsonl" %N% "%MK%\cf_px_7b.done" >> "%LOG%" 2>&1

:c4
if exist "%MK%\cf_px_3b.done" goto c5
echo [confirm] pixel VLM 3B %time% >> "%LOG%"
%PY% scripts\pilot\run_pixel_retry.py --subset %QA% --dataroot . --model qwen2.5vl:3b --out %P10%\results_cf_px_3b >> "%LOG%" 2>&1
%PY% scripts\audit\mark_if_complete.py "%P10%\results_cf_px_3b\pixel__clean__forced.jsonl" %N% "%MK%\cf_px_3b.done" >> "%LOG%" 2>&1

:c5
if exist "%MK%\cf_v9_7b.done" goto c6
echo [confirm] v9 serializer 7B %time% >> "%LOG%"
%PY% scripts\coda\run_coda_text_v9.py --qa %QA% --states %ST% --model qwen2.5:7b --out %P10%\results_cf_v9_7b >> "%LOG%" 2>&1
%PY% scripts\audit\mark_if_complete.py "%P10%\results_cf_v9_7b\state_typed__clean__forced.jsonl" %N% "%MK%\cf_v9_7b.done" >> "%LOG%" 2>&1

:c6
if exist "%MK%\cf_v9_3b.done" goto fin
echo [confirm] v9 serializer 3B %time% >> "%LOG%"
%PY% scripts\coda\run_coda_text_v9.py --qa %QA% --states %ST% --model qwen2.5:3b --out %P10%\results_cf_v9_3b >> "%LOG%" 2>&1
%PY% scripts\audit\mark_if_complete.py "%P10%\results_cf_v9_3b\state_typed__clean__forced.jsonl" %N% "%MK%\cf_v9_3b.done" >> "%LOG%" 2>&1

:fin
set OK=1
if not exist "%MK%\cf_v15_7b.done" set OK=0
if not exist "%MK%\cf_v15_3b.done" set OK=0
if not exist "%MK%\cf_px_7b.done" set OK=0
if not exist "%MK%\cf_px_3b.done" set OK=0
if "%OK%"=="1" echo done > outputs\CONFIRM_COMPLETE.marker
echo ==== CONFIRM END %date% %time% ==== >> "%LOG%"
