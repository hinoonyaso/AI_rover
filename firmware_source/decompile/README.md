# RosRobotControllerM4 HEX 역컴파일

원본: `../RosRobotControllerM4.zip` 안의 `RosRobotControllerM4.hex`.
대상: STM32F4 Cortex-M4, Thumb, 플래시 시작 주소 `0x08000000`.

## 산출물

- `RosRobotControllerM4.hex`: ZIP에서 추출한 원본 HEX. ZIP 내부 파일과 바이트 단위로 동일하다.
- `RosRobotControllerM4.bin`: Intel HEX 레코드의 절대 주소를 기준으로 만든 연속 바이너리. 미기록 주소가 있으면 `0xFF`로 채운다.
- `decompiled.c`: Ghidra 12.1.4가 찾아낸 함수의 C 형태 의사 코드. **원본 C도 아니고 바로 빌드 가능한 소스도 아니다.**
- `functions.tsv`: 함수 진입 주소, Ghidra 함수명, 역컴파일 성공 여부.
- `ghidra_project/`: 분석된 Ghidra 프로젝트. `RosRobotControllerM4.gpr`을 열어 함수 그래프와 참조를 계속 조사할 수 있다.
- `vectors.tsv`: Cortex-M 벡터표의 앞 98개 엔트리. 같은 핸들러를 여러 IRQ가 공유할 수 있다.
- `disassembly_thumb.txt`: GNU objdump로 생성한 Thumb 역어셈블. 데이터와 문자열까지 기계적으로 명령으로 읽으므로 코드 경계의 증거로 단독 사용하면 안 된다.
- `strings.txt`: 바이너리에서 발견한 5자 이상 문자열. 첫 열은 `0x08000000` 기준 파일 오프셋이다.
- `SeedVectors.java`, `ExportDecomp.java`: 재분석용 Ghidra headless 스크립트.
- `ghidra.log`, `scripts.log`: 성공한 분석의 로그. `ghidra_setup_attempts.log`에는 ARM64 도구 준비 전의 시행착오를 보관했다.

## 확인된 이미지 정보

- ZIP SHA-256: `a673f23ead59b1c5fc9a0b6dc0c1e28048a9c543f0614721fc788dfd853f1ae4`
- 추출 HEX SHA-256: `c1b9983050d2d192809850d1e548bcfae2adf544eed1f90e9df87198c38394c2`
- BIN SHA-256: `b470e9314bb741589c72ca5b4cd530fc82720408d425df77e4229b9d5e57b87a`
- HEX 데이터 주소 범위: `0x08000000`–`0x080140DF` (82,144바이트)
- 초기 스택 포인터: `0x2001FCC8`; Reset 벡터: `0x0800026D` (Thumb 표시 비트 포함).
- 모든 Intel HEX 레코드 체크섬을 검증했다.
- Ghidra가 493개 함수를 식별했고 모두 의사 C로 내보냈다 (디컴파일 실패 0건). 벡터표에서 서로 다른 함수 시작점 31개를 지정했다.

## 읽을 때 주의할 점

`decompiled.c`의 `FUN_0800635c`처럼 `FUN_`으로 시작하는 이름은 주소에서 만든 임시 이름이다. 예를 들어 이 함수에는 `0x40003000`(IWDG 주소), prescaler 값 `3`, reload 값 `0x13`이 보이지만, 함수명과 주변장치 의미는 수동 분석을 거쳐 확정해야 한다. `Reset_Handler`는 벡터표에서 붙인 이름이며, 일부 간접 호출이나 점프 테이블에는 Ghidra 경고가 남아 있다. 이 493개는 Ghidra가 찾아낸 함수 수이지 펌웨어에 존재하는 모든 함수가 빠짐없이 복원됐다는 뜻은 아니다.

## 재현

Ghidra 12.1.4를 준비한다. Linux ARM64에서는 공식 배포본에 네이티브 디컴파일러가 없으므로 Ghidra의 `support/gradle`에서 `./gradlew buildNatives`를 먼저 실행한다. 아래 명령은 이 폴더에서 실행한다. `GHIDRA_DIR`은 설치 디렉터리로 바꾼다.

```sh
GHIDRA_DIR=/path/to/ghidra_12.1.4_PUBLIC
unzip -p ../RosRobotControllerM4.zip RosRobotControllerM4.hex > RosRobotControllerM4.hex
arm-none-eabi-objcopy -I ihex -O binary RosRobotControllerM4.hex RosRobotControllerM4.bin
mkdir -p /tmp/jetrover-ghidra
"$GHIDRA_DIR/support/analyzeHeadless" /tmp/jetrover-ghidra RosRobotControllerM4 \
  -import RosRobotControllerM4.hex \
  -processor ARM:LE:32:Cortex -cspec default \
  -scriptPath . -preScript SeedVectors.java \
  -postScript ExportDecomp.java "$PWD" \
  -analysisTimeoutPerFile 1800 -max-cpu 4
```

Ghidra 도구 설치본은 `decompile`에 포함하지 않았다. 함수 이름과 자료형은 대부분 기계적 추정이며, 주변장치 레지스터 이름과 실제 동작은 수동 검증이 필요하다. 이 결과만으로 기존 보드에 펌웨어를 올리면 안 된다.
