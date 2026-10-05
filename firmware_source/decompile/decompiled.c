/* Ghidra C-like pseudocode. Not original or directly buildable source.
 * Input: RosRobotControllerM4.hex, Cortex-M Thumb, flash 0x08000000.
 */

/* 08000190 */

void FUN_08000190(void)

{
  undefined4 uVar1;
  uint uVar2;
  undefined4 *puVar3;
  undefined4 *puVar4;
  undefined4 *puVar5;
  undefined4 *puVar6;
  
  puVar3 = (undefined4 *)((int)&DAT_080001e4 + DAT_080001e4);
  puVar4 = (undefined4 *)((int)&DAT_080001e4 + DAT_080001e8);
  do {
    if (puVar3 == puVar4) {
      FUN_0800024e();
    }
    uVar1 = *puVar3;
    puVar5 = puVar3 + 1;
    puVar6 = puVar3 + 2;
    puVar3 = puVar3 + 4;
    uVar2 = (int)puVar3 - ((int)&DAT_080001e4 + DAT_080001e4);
    if ((uint)(DAT_080001e8 - DAT_080001e4) >> 4 <= (uVar2 >> 4 | uVar2 * 0x10000000) - 1) {
      FUN_0800024e(uVar1,*puVar5,*puVar6);
    }
    FUN_080001e2();
  } while( true );
}



/* 080001e2 */

void FUN_080001e2(void)

{
  code *UNRECOVERED_JUMPTABLE;
  
                    /* WARNING: Could not recover jumptable at 0x080001e2. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*UNRECOVERED_JUMPTABLE)();
  return;
}



/* 08000228 */

undefined4 FUN_08000228(uint *param_1,int param_2,uint *param_3)

{
  uint uVar1;
  undefined4 uVar2;
  int iVar3;
  int iVar4;
  undefined1 *puVar5;
  int iVar6;
  int iVar7;
  
  if (param_2 != 100) {
    return 0;
  }
  iVar4 = 0;
  uVar1 = *param_3;
  puVar5 = (undefined1 *)0x80004f8;
  if ((int)uVar1 < 0) {
    uVar1 = -uVar1;
    puVar5 = &DAT_080004fc;
  }
  else if ((int)(*param_1 << 0x1e) < 0) {
    puVar5 = (undefined1 *)0x8000500;
  }
  else {
    if (-1 < (int)(*param_1 << 0x1d)) goto LAB_080004c8;
    puVar5 = (undefined1 *)0x8000504;
  }
  iVar4 = 1;
LAB_080004c8:
  iVar3 = 0;
  for (; uVar1 != 0; uVar1 = uVar1 / 10) {
    *(byte *)((int)param_1 + iVar3 + 0x24) = (char)uVar1 + (char)(uVar1 / 10) * -10 + 0x30;
    iVar3 = iVar3 + 1;
  }
  if ((int)(*param_1 << 0x1a) < 0) {
    uVar1 = param_1[7];
    *param_1 = *param_1 & 0xffffffef;
  }
  else {
    uVar1 = 1;
  }
  if (iVar3 < (int)uVar1) {
    iVar7 = uVar1 - iVar3;
  }
  else {
    iVar7 = 0;
  }
  param_1[6] = param_1[6] - (iVar7 + iVar3 + iVar4);
  if (-1 < (int)((uint)(byte)*param_1 << 0x1b)) {
    FUN_08000440(param_1);
  }
  for (iVar6 = 0; iVar6 < iVar4; iVar6 = iVar6 + 1) {
    (*(code *)param_1[1])(puVar5[iVar6],param_1[2]);
    param_1[8] = param_1[8] + 1;
  }
  if ((int)((uint)(byte)*param_1 << 0x1b) < 0) {
    FUN_08000440(param_1);
  }
  while (0 < iVar7) {
    (*(code *)param_1[1])(0x30,param_1[2]);
    param_1[8] = param_1[8] + 1;
    iVar7 = iVar7 + -1;
  }
  while (0 < iVar3) {
    (*(code *)param_1[1])(*(byte *)((int)param_1 + iVar3 + 0x23),param_1[2]);
    param_1[8] = param_1[8] + 1;
    iVar3 = iVar3 + -1;
  }
  FUN_0800046c(param_1);
  if ((int)((uint)(byte)*param_1 << 0x18) < 0) {
    uVar2 = 2;
  }
  else {
    uVar2 = 1;
  }
  return uVar2;
}



/* 08000232 */

undefined8 FUN_08000232(undefined4 param_1,undefined4 param_2)

{
  FUN_080132a4();
  FUN_08000894(param_1,param_2);
  FUN_08000cd8();
  return CONCAT44(param_2,param_1);
}



/* 08000246 */

void FUN_08000246(void)

{
  FUN_08000daa();
  return;
}



/* 0800024e */

void FUN_0800024e(void)

{
  undefined4 uVar1;
  undefined4 extraout_r2;
  undefined8 uVar2;
  
  uVar1 = FUN_08000e1e();
  FUN_08000232(uVar1,extraout_r2);
  FUN_0800cc9c();
  uVar2 = FUN_080010f4();
  FUN_08000246();
  FUN_0800b630((int)uVar2,(int)((ulonglong)uVar2 >> 0x20));
  (*DAT_08000294)();
                    /* WARNING: Could not recover jumptable at 0x08000272. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*DAT_08000298)();
  return;
}



/* 0800026c */

void Reset_Handler(void)

{
  (*DAT_08000294)();
                    /* WARNING: Could not recover jumptable at 0x08000272. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*DAT_08000298)();
  return;
}



/* 08000286 */

void IRQ_0_Handler(void)

{
  do {
                    /* WARNING: Do nothing block with infinite loop */
  } while( true );
}



/* 08000288 */

undefined8 FUN_08000288(void)

{
  return CONCAT44(DAT_080002a0,DAT_0800029c);
}



/* 080002ae */

int FUN_080002ae(uint param_1,uint param_2)

{
  int iVar1;
  int iVar2;
  
  iVar2 = (int)((ulonglong)param_1 * (ulonglong)param_2);
  if ((int)((ulonglong)param_1 * (ulonglong)param_2 >> 0x20) == 0) {
    iVar1 = FUN_080008f2(iVar2,0,-1 - iVar2);
    if (iVar1 != 0) {
      FUN_08000744(iVar1,iVar2);
    }
    return iVar1;
  }
  return 0;
}



/* 080002d8 */

void FUN_080002d8(int param_1)

{
  int *piVar1;
  int *piVar2;
  int *piVar3;
  
  piVar3 = (int *)(param_1 + -4);
  piVar1 = (int *)FUN_0800085c();
  if (param_1 == 0) {
    return;
  }
  piVar2 = (int *)*piVar1;
  for (piVar1 = (int *)((int *)*piVar1)[1]; piVar1 != (int *)0x0 && piVar1 < piVar3;
      piVar1 = (int *)piVar1[1]) {
    piVar2 = piVar1;
  }
  if ((int *)(*piVar2 + (int)piVar2) == piVar3) {
    *piVar2 = *piVar2 + *piVar3;
  }
  else {
    piVar2[1] = (int)piVar3;
    piVar2 = piVar3;
  }
  if ((int *)(*piVar2 + (int)piVar2) == piVar1) {
    piVar2[1] = piVar1[1];
    *piVar2 = *piVar2 + *piVar1;
    return;
  }
  piVar2[1] = (int)piVar1;
  return;
}



/* 08000326 */

undefined8 FUN_08000326(uint param_1,uint param_2,uint param_3,uint param_4)

{
  undefined4 uVar1;
  uint uVar2;
  uint uVar3;
  int iVar4;
  uint uVar5;
  uint uVar6;
  uint uVar7;
  int iVar8;
  uint uVar9;
  uint uVar10;
  bool bVar11;
  
  if (param_4 == 0 && param_3 == 0) {
    uVar1 = 0;
    if (param_1 != 0 || param_2 != 0) {
      uVar1 = 0xffffffff;
    }
    return CONCAT44(uVar1,uVar1);
  }
  uVar6 = 0;
  if (param_4 != 0) {
    iVar4 = LZCOUNT(param_4);
    uVar2 = param_4 << iVar4;
    uVar6 = uVar2 >> iVar4 ^ param_4 | param_3;
  }
  else {
    iVar4 = LZCOUNT(param_3);
    uVar2 = param_3 << iVar4;
  }
  uVar5 = -iVar4 + 0x20;
  if (param_4 != 0) {
    uVar2 = uVar2 | param_3 >> (uVar5 & 0xff);
    uVar5 = -iVar4 + 0x40;
  }
  uVar3 = uVar2 >> 0x10;
  if (uVar6 != 0 || (uVar2 & 0xffff) != 0) {
    uVar3 = uVar3 + 1;
  }
  iVar4 = 0;
  uVar6 = 0;
  for (; param_4 < param_2 || param_2 - param_4 < (uint)(param_3 <= param_1);
      param_2 = (param_2 -
                (uVar7 * param_4 +
                uVar9 * param_3 + (int)((ulonglong)uVar7 * (ulonglong)param_3 >> 0x20))) -
                (uint)bVar11) {
    if (param_2 != 0) {
      iVar8 = LZCOUNT(param_2);
      uVar2 = param_2 << iVar8;
    }
    else {
      iVar8 = LZCOUNT(param_1);
      uVar2 = param_1 << iVar8;
    }
    uVar9 = -iVar8 + 0x20;
    if (param_2 != 0) {
      uVar2 = uVar2 | param_1 >> (uVar9 & 0xff);
      uVar9 = -iVar8 + 0x40;
    }
    uVar10 = (uVar9 - uVar5) - 0x10;
    uVar7 = uVar2 / uVar3 >> (0x20 - (uVar10 & 0x1f) & 0xff);
    uVar9 = uVar7;
    uVar2 = uVar2 / uVar3 << (uVar10 & 0x1f);
    if ((int)uVar10 < 0) {
      uVar9 = 0;
      uVar2 = uVar7;
    }
    uVar7 = uVar2;
    if (0x1f < (int)uVar10) {
      uVar7 = 0;
      uVar9 = uVar2;
    }
    if (uVar7 == 0 && uVar9 == 0) {
      uVar7 = 1;
    }
    bVar11 = CARRY4(uVar6,uVar7);
    uVar6 = uVar6 + uVar7;
    iVar4 = iVar4 + uVar9 + bVar11;
    uVar2 = (uint)((ulonglong)uVar7 * (ulonglong)param_3);
    bVar11 = param_1 < uVar2;
    param_1 = param_1 - uVar2;
  }
  return CONCAT44(iVar4,uVar6);
}



/* 08000418 */

void FUN_08000418(undefined4 param_1,undefined4 param_2,undefined4 param_3,undefined4 param_4)

{
  undefined4 local_20;
  undefined4 uStack_1c;
  undefined4 uStack_8;
  undefined4 uStack_4;
  
  local_20 = param_1;
  uStack_1c = param_4;
  uStack_8 = param_3;
  uStack_4 = param_4;
  FUN_08000a0e(param_2,&local_20,&uStack_8,DAT_0800043c + 0x8000424);
  FUN_08000a34(0,&local_20);
  return;
}



/* 08000440 */

void FUN_08000440(uint *param_1)

{
  uint uVar1;
  undefined4 uVar2;
  
  uVar1 = param_1[6];
  if ((int)(*param_1 << 0x1b) < 0) {
    uVar2 = 0x30;
  }
  else {
    uVar2 = 0x20;
  }
  if ((*param_1 & 1) != 0) {
    return;
  }
  while (uVar1 = uVar1 - 1, -1 < (int)uVar1) {
    (*(code *)param_1[1])(uVar2,param_1[2]);
    param_1[8] = param_1[8] + 1;
  }
  return;
}



/* 0800046c */

void FUN_0800046c(byte *param_1)

{
  int iVar1;
  
  iVar1 = *(int *)(param_1 + 0x18);
  if ((*param_1 & 1) == 0) {
    return;
  }
  while (iVar1 = iVar1 + -1, -1 < iVar1) {
    (**(code **)(param_1 + 4))(0x20,*(undefined4 *)(param_1 + 8));
    *(int *)(param_1 + 0x20) = *(int *)(param_1 + 0x20) + 1;
  }
  return;
}



/* 08000490 */

undefined4 FUN_08000490(uint *param_1,int param_2,uint *param_3)

{
  uint uVar1;
  undefined4 uVar2;
  int iVar3;
  int iVar4;
  undefined1 *puVar5;
  int iVar6;
  int iVar7;
  
  iVar4 = 0;
  uVar1 = *param_3;
  puVar5 = (undefined1 *)0x80004f8;
  if (param_2 != 0x75) {
    if ((int)uVar1 < 0) {
      uVar1 = -uVar1;
      puVar5 = &DAT_080004fc;
    }
    else if ((int)(*param_1 << 0x1e) < 0) {
      puVar5 = (undefined1 *)0x8000500;
    }
    else {
      if (-1 < (int)(*param_1 << 0x1d)) goto LAB_080004c8;
      puVar5 = (undefined1 *)0x8000504;
    }
    iVar4 = 1;
  }
LAB_080004c8:
  iVar3 = 0;
  for (; uVar1 != 0; uVar1 = uVar1 / 10) {
    *(byte *)((int)param_1 + iVar3 + 0x24) = (char)uVar1 + (char)(uVar1 / 10) * -10 + 0x30;
    iVar3 = iVar3 + 1;
  }
  if ((int)(*param_1 << 0x1a) < 0) {
    uVar1 = param_1[7];
    *param_1 = *param_1 & 0xffffffef;
  }
  else {
    uVar1 = 1;
  }
  if (iVar3 < (int)uVar1) {
    iVar7 = uVar1 - iVar3;
  }
  else {
    iVar7 = 0;
  }
  param_1[6] = param_1[6] - (iVar7 + iVar3 + iVar4);
  if (-1 < (int)((uint)(byte)*param_1 << 0x1b)) {
    FUN_08000440(param_1);
  }
  for (iVar6 = 0; iVar6 < iVar4; iVar6 = iVar6 + 1) {
    (*(code *)param_1[1])(puVar5[iVar6],param_1[2]);
    param_1[8] = param_1[8] + 1;
  }
  if ((int)((uint)(byte)*param_1 << 0x1b) < 0) {
    FUN_08000440(param_1);
  }
  while (0 < iVar7) {
    (*(code *)param_1[1])(0x30,param_1[2]);
    param_1[8] = param_1[8] + 1;
    iVar7 = iVar7 + -1;
  }
  while (0 < iVar3) {
    (*(code *)param_1[1])(*(byte *)((int)param_1 + iVar3 + 0x23),param_1[2]);
    param_1[8] = param_1[8] + 1;
    iVar3 = iVar3 + -1;
  }
  FUN_0800046c(param_1);
  if ((int)((uint)(byte)*param_1 << 0x18) < 0) {
    uVar2 = 2;
  }
  else {
    uVar2 = 1;
  }
  return uVar2;
}



/* 08000508 */

uint FUN_08000508(uint *param_1,uint *param_2)

{
  int iVar1;
  uint uVar2;
  int iVar3;
  uint uVar4;
  int iVar5;
  uint *puVar6;
  
  iVar1 = DAT_0800063c;
  param_1[8] = 0;
  while (uVar2 = (*(code *)param_1[3])(param_1), uVar2 != 0) {
    if (uVar2 == 0x25) {
      uVar4 = 0;
      while (((uVar2 = (*(code *)param_1[3])(param_1), 0x1f < (int)uVar2 && (uVar2 < 0x31)) &&
             ((byte)(&DAT_080004fc)[iVar1 + uVar2] != 0))) {
        uVar4 = uVar4 | (byte)(&DAT_080004fc)[iVar1 + uVar2];
      }
      if ((int)(uVar4 << 0x1e) < 0) {
        uVar4 = uVar4 & 0xfffffffb;
      }
      param_1[7] = 0;
      iVar5 = 0;
      param_1[6] = 0;
      puVar6 = param_2;
      do {
        if (uVar2 == 0x2a) {
          param_2 = puVar6 + 1;
          param_1[iVar5 + 6] = *puVar6;
          uVar2 = (*(code *)param_1[3])(param_1);
          if (iVar5 == 1) {
            if ((int)param_1[7] < 0) {
              uVar4 = uVar4 & 0xffffffdf;
            }
            break;
          }
        }
        else {
          iVar3 = FUN_0801327a(uVar2);
          if (iVar3 != 0) {
            param_1[iVar5 + 6] = uVar2 - 0x30;
            while( true ) {
              uVar2 = (*(code *)param_1[3])(param_1);
              iVar3 = FUN_0801327a();
              if (iVar3 == 0) break;
              param_1[iVar5 + 6] = (uVar2 + param_1[iVar5 + 6] * 10) - 0x30;
            }
          }
          param_2 = puVar6;
          if (iVar5 == 1) break;
        }
        if (uVar2 != 0x2e) break;
        uVar2 = (*(code *)param_1[3])(param_1);
        iVar5 = iVar5 + 1;
        uVar4 = uVar4 | 0x20;
        puVar6 = param_2;
      } while (iVar5 < 2);
      if ((int)param_1[6] < 0) {
        uVar4 = uVar4 | 1;
        param_1[6] = -param_1[6];
      }
      if ((uVar4 & 1) != 0) {
        uVar4 = uVar4 & 0xffffffef;
      }
      if (uVar2 == 0) break;
      if (uVar2 - 0x41 < 0x1a) {
        uVar2 = uVar2 + 0x20;
        uVar4 = uVar4 | 0x800;
      }
      *param_1 = uVar4;
      iVar5 = FUN_08000228(param_1,uVar2,param_2);
      if (iVar5 == 0) goto LAB_0800052c;
      if (iVar5 == 1) {
        param_2 = param_2 + 1;
      }
      else {
        param_2 = (uint *)(((int)param_2 + 7U & 0xfffffff8) + 8);
      }
    }
    else {
LAB_0800052c:
      (*(code *)param_1[1])(uVar2,param_1[2]);
      param_1[8] = param_1[8] + 1;
    }
  }
  return param_1[8];
}



/* 08000640 */

undefined4 FUN_08000640(char *param_1)

{
  int iVar1;
  undefined4 uVar2;
  
  do {
    if (*param_1 == '\0') {
      uVar2 = FUN_08013288(10,DAT_08000668);
      return uVar2;
    }
    iVar1 = FUN_08013288(*param_1,DAT_08000668);
    param_1 = param_1 + 1;
  } while (iVar1 != -1);
  return 0xffffffff;
}



/* 0800066c */

int FUN_0800066c(uint *param_1)

{
  uint *puVar1;
  uint *puVar2;
  int iVar3;
  uint uVar4;
  
  puVar2 = param_1;
  while (((uint)puVar2 & 3) != 0) {
    puVar1 = (uint *)((int)puVar2 + 1);
    uVar4 = *puVar2;
    puVar2 = puVar1;
    if ((char)uVar4 == '\0') {
      return (int)puVar1 - ((int)param_1 + 1);
    }
  }
  do {
    uVar4 = *puVar2;
    puVar2 = puVar2 + 1;
    uVar4 = uVar4 + 0xfefefeff & ~uVar4;
  } while ((uVar4 & 0x80808080) == 0);
  iVar3 = (int)puVar2 - (int)((int)param_1 + 1);
  if ((uVar4 & 0x80) == 0) {
    if ((uVar4 & 0x8080) == 0) {
      if ((uVar4 & 0x808080) != 0) {
        return iVar3 + -1;
      }
    }
    else {
      iVar3 = iVar3 + -2;
    }
    return iVar3;
  }
  return iVar3 + -3;
}



/* 080006aa */

undefined8 FUN_080006aa(uint *param_1,uint *param_2,uint param_3,uint param_4)

{
  bool bVar1;
  uint *puVar2;
  uint *puVar3;
  uint *puVar4;
  byte *pbVar5;
  byte bVar6;
  undefined2 uVar7;
  byte in_r12;
  uint uVar8;
  uint uVar9;
  uint uVar10;
  uint uVar11;
  uint uVar12;
  bool bVar13;
  
  puVar4 = param_2;
  if (3 < param_3) {
    uVar8 = (uint)param_1 & 3;
    puVar2 = param_1;
    uVar9 = uVar8;
    if (uVar8 != 0) {
      bVar6 = (byte)*param_2;
      puVar4 = (uint *)((int)param_2 + 1);
      if (uVar8 < 3) {
        puVar4 = (uint *)((int)param_2 + 2);
        uVar9 = (uint)*(byte *)((int)param_2 + 1);
      }
      *(byte *)param_1 = bVar6;
      param_2 = puVar4;
      if (uVar8 < 2) {
        param_2 = (uint *)((int)puVar4 + 1);
        bVar6 = (byte)*puVar4;
      }
      param_3 = (param_3 + uVar8) - 4;
      puVar4 = (uint *)((int)param_1 + 1);
      if (uVar8 < 3) {
        puVar4 = (uint *)((int)param_1 + 2);
        *(byte *)((int)param_1 + 1) = (byte)uVar9;
      }
      puVar2 = puVar4;
      if (uVar8 < 2) {
        puVar2 = (uint *)((int)puVar4 + 1);
        *(byte *)puVar4 = bVar6;
      }
    }
    param_4 = (uint)param_2 & 3;
    if (param_4 == 0) {
      uVar9 = 0;
      while (uVar8 = param_3 - 0x20, 0x1f < param_3) {
        uVar9 = param_2[1];
        uVar10 = param_2[2];
        uVar11 = param_2[3];
        *puVar2 = *param_2;
        puVar2[1] = uVar9;
        puVar2[2] = uVar10;
        puVar2[3] = uVar11;
        uVar9 = param_2[4];
        uVar10 = param_2[5];
        uVar11 = param_2[6];
        uVar12 = param_2[7];
        param_2 = param_2 + 8;
        puVar2[4] = uVar9;
        puVar2[5] = uVar10;
        puVar2[6] = uVar11;
        puVar2[7] = uVar12;
        puVar2 = puVar2 + 8;
        param_3 = uVar8;
      }
      if ((uVar8 & 0x10) != 0) {
        uVar9 = *param_2;
        uVar10 = param_2[1];
        uVar11 = param_2[2];
        uVar12 = param_2[3];
        param_2 = param_2 + 4;
        *puVar2 = uVar9;
        puVar2[1] = uVar10;
        puVar2[2] = uVar11;
        puVar2[3] = uVar12;
        puVar2 = puVar2 + 4;
      }
      if ((int)(param_3 << 0x1c) < 0) {
        uVar9 = *param_2;
        uVar10 = param_2[1];
        param_2 = param_2 + 2;
        *puVar2 = uVar9;
        puVar2[1] = uVar10;
        puVar2 = puVar2 + 2;
      }
      puVar3 = puVar2;
      puVar4 = param_2;
      if ((uVar8 & 4) != 0) {
        puVar4 = param_2 + 1;
        uVar9 = *param_2;
        puVar3 = puVar2 + 1;
        *puVar2 = uVar9;
      }
      uVar7 = (undefined2)uVar9;
      if ((uVar8 & 3) != 0) {
        bVar1 = (uVar8 & 2) != 0;
        param_3 = param_3 << 0x1f;
        bVar13 = (int)param_3 < 0;
        puVar2 = puVar4;
        if (bVar1) {
          puVar2 = (uint *)((int)puVar4 + 2);
          uVar7 = (undefined2)*puVar4;
        }
        puVar4 = puVar2;
        if (bVar13) {
          puVar4 = (uint *)((int)puVar2 + 1);
          param_3 = (uint)(byte)*puVar2;
        }
        puVar2 = puVar3;
        if (bVar1) {
          puVar2 = (uint *)((int)puVar3 + 2);
          *(undefined2 *)puVar3 = uVar7;
        }
        puVar3 = puVar2;
        if (bVar13) {
          puVar3 = (uint *)((int)puVar2 + 1);
          *(byte *)puVar2 = (byte)param_3;
        }
        return CONCAT44(puVar4,puVar3);
      }
      return CONCAT44(puVar4,puVar3);
    }
    while( true ) {
      in_r12 = (byte)uVar9;
      if (param_3 < 8) break;
      puVar4 = param_2 + 1;
      param_4 = *param_2;
      param_2 = param_2 + 2;
      uVar9 = *puVar4;
      *puVar2 = param_4;
      puVar2[1] = uVar9;
      puVar2 = puVar2 + 2;
      param_3 = param_3 - 8;
    }
    param_3 = param_3 - 4;
    param_1 = puVar2;
    puVar4 = param_2;
    if (-1 < (int)param_3) {
      puVar4 = param_2 + 1;
      param_4 = *param_2;
      param_1 = puVar2 + 1;
      *puVar2 = param_4;
    }
  }
  bVar6 = (byte)param_4;
  bVar1 = (param_3 & 2) != 0;
  param_3 = param_3 << 0x1f;
  bVar13 = (int)param_3 < 0;
  if (bVar1) {
    pbVar5 = (byte *)((int)puVar4 + 1);
    bVar6 = (byte)*puVar4;
    puVar4 = (uint *)((int)puVar4 + 2);
    in_r12 = *pbVar5;
  }
  puVar2 = puVar4;
  if (bVar13) {
    puVar2 = (uint *)((int)puVar4 + 1);
    param_3 = (uint)(byte)*puVar4;
  }
  if (bVar1) {
    pbVar5 = (byte *)((int)param_1 + 1);
    *(byte *)param_1 = bVar6;
    param_1 = (uint *)((int)param_1 + 2);
    *pbVar5 = in_r12;
  }
  puVar4 = param_1;
  if (bVar13) {
    puVar4 = (uint *)((int)param_1 + 1);
    *(byte *)param_1 = (byte)param_3;
  }
  return CONCAT44(puVar2,puVar4);
}



/* 08000734 */

undefined4 * FUN_08000734(undefined4 *param_1,uint param_2,undefined1 param_3)

{
  undefined2 uVar1;
  undefined4 *puVar2;
  undefined4 *puVar3;
  uint uVar4;
  undefined4 uVar5;
  bool bVar6;
  
  uVar1 = CONCAT11(param_3,param_3);
  uVar5 = CONCAT22(uVar1,uVar1);
  bVar6 = 0x1f < param_2;
  param_2 = param_2 - 0x20;
  do {
    if (bVar6) {
      *param_1 = uVar5;
      param_1[1] = uVar5;
      param_1[2] = uVar5;
      param_1[3] = uVar5;
      param_1[4] = uVar5;
      param_1[5] = uVar5;
      param_1[6] = uVar5;
      param_1[7] = uVar5;
      param_1 = param_1 + 8;
      bVar6 = 0x1f < param_2;
      param_2 = param_2 - 0x20;
    }
  } while (bVar6);
  if ((param_2 & 0x10) != 0) {
    *param_1 = uVar5;
    param_1[1] = uVar5;
    param_1[2] = uVar5;
    param_1[3] = uVar5;
    param_1 = param_1 + 4;
  }
  if ((int)(param_2 << 0x1c) < 0) {
    *param_1 = uVar5;
    param_1[1] = uVar5;
    param_1 = param_1 + 2;
  }
  uVar4 = param_2 << 0x1e;
  puVar3 = param_1;
  if ((param_2 << 0x1c & 0x40000000) != 0) {
    puVar3 = param_1 + 1;
    *param_1 = uVar5;
  }
  if (uVar4 != 0) {
    puVar2 = puVar3;
    if ((int)uVar4 < 0) {
      puVar2 = (undefined4 *)((int)puVar3 + 2);
      *(undefined2 *)puVar3 = uVar1;
    }
    puVar3 = puVar2;
    if ((uVar4 & 0x40000000) != 0) {
      puVar3 = (undefined4 *)((int)puVar2 + 1);
      *(undefined1 *)puVar2 = param_3;
    }
    return puVar3;
  }
  return puVar3;
}



/* 08000744 */

undefined4 * FUN_08000744(undefined4 *param_1,uint param_2)

{
  undefined4 *puVar1;
  undefined1 *puVar2;
  undefined4 *puVar3;
  uint uVar4;
  int iVar5;
  bool bVar6;
  
  if (param_2 < 4) {
    if ((param_2 & 2) != 0) {
      puVar2 = (undefined1 *)((int)param_1 + 1);
      *(undefined1 *)param_1 = 0;
      param_1 = (undefined4 *)((int)param_1 + 2);
      *puVar2 = 0;
    }
    puVar1 = param_1;
    if ((int)(param_2 << 0x1f) < 0) {
      puVar1 = (undefined4 *)((int)param_1 + 1);
      *(undefined1 *)param_1 = 0;
    }
    return puVar1;
  }
  if (((uint)param_1 & 3) != 0) {
    iVar5 = 4 - ((uint)param_1 & 3);
    puVar1 = param_1;
    if (iVar5 != 2) {
      puVar1 = (undefined4 *)((int)param_1 + 1);
      *(undefined1 *)param_1 = 0;
    }
    param_1 = puVar1;
    if (1 < iVar5) {
      param_1 = (undefined4 *)((int)puVar1 + 2);
      *(undefined2 *)puVar1 = 0;
    }
    param_2 = param_2 - iVar5;
  }
  bVar6 = 0x1f < param_2;
  param_2 = param_2 - 0x20;
  do {
    if (bVar6) {
      *param_1 = 0;
      param_1[1] = 0;
      param_1[2] = 0;
      param_1[3] = 0;
      param_1[4] = 0;
      param_1[5] = 0;
      param_1[6] = 0;
      param_1[7] = 0;
      param_1 = param_1 + 8;
      bVar6 = 0x1f < param_2;
      param_2 = param_2 - 0x20;
    }
  } while (bVar6);
  if ((param_2 & 0x10) != 0) {
    *param_1 = 0;
    param_1[1] = 0;
    param_1[2] = 0;
    param_1[3] = 0;
    param_1 = param_1 + 4;
  }
  if ((int)(param_2 << 0x1c) < 0) {
    *param_1 = 0;
    param_1[1] = 0;
    param_1 = param_1 + 2;
  }
  uVar4 = param_2 << 0x1e;
  puVar1 = param_1;
  if ((param_2 << 0x1c & 0x40000000) != 0) {
    puVar1 = param_1 + 1;
    *param_1 = 0;
  }
  if (uVar4 != 0) {
    puVar3 = puVar1;
    if ((int)uVar4 < 0) {
      puVar3 = (undefined4 *)((int)puVar1 + 2);
      *(undefined2 *)puVar1 = 0;
    }
    puVar1 = puVar3;
    if ((uVar4 & 0x40000000) != 0) {
      puVar1 = (undefined4 *)((int)puVar3 + 1);
      *(undefined1 *)puVar3 = 0;
    }
    return puVar1;
  }
  return puVar1;
}



/* 08000788 */

undefined4 * FUN_08000788(undefined4 *param_1,uint param_2)

{
  undefined4 *puVar1;
  undefined4 *puVar2;
  uint uVar3;
  bool bVar4;
  
  bVar4 = 0x1f < param_2;
  param_2 = param_2 - 0x20;
  do {
    if (bVar4) {
      *param_1 = 0;
      param_1[1] = 0;
      param_1[2] = 0;
      param_1[3] = 0;
      param_1[4] = 0;
      param_1[5] = 0;
      param_1[6] = 0;
      param_1[7] = 0;
      param_1 = param_1 + 8;
      bVar4 = 0x1f < param_2;
      param_2 = param_2 - 0x20;
    }
  } while (bVar4);
  if ((param_2 & 0x10) != 0) {
    *param_1 = 0;
    param_1[1] = 0;
    param_1[2] = 0;
    param_1[3] = 0;
    param_1 = param_1 + 4;
  }
  if ((int)(param_2 << 0x1c) < 0) {
    *param_1 = 0;
    param_1[1] = 0;
    param_1 = param_1 + 2;
  }
  uVar3 = param_2 << 0x1e;
  puVar2 = param_1;
  if ((param_2 << 0x1c & 0x40000000) != 0) {
    puVar2 = param_1 + 1;
    *param_1 = 0;
  }
  if (uVar3 != 0) {
    puVar1 = puVar2;
    if ((int)uVar3 < 0) {
      puVar1 = (undefined4 *)((int)puVar2 + 2);
      *(undefined2 *)puVar2 = 0;
    }
    puVar2 = puVar1;
    if ((uVar3 & 0x40000000) != 0) {
      puVar2 = (undefined4 *)((int)puVar1 + 1);
      *(undefined1 *)puVar1 = 0;
    }
    return puVar2;
  }
  return puVar2;
}



/* 080007d8 */

int FUN_080007d8(uint *param_1,uint *param_2)

{
  undefined4 uVar1;
  undefined4 uVar2;
  undefined4 uVar3;
  undefined4 uVar4;
  uint *puVar5;
  uint *puVar6;
  uint uVar7;
  uint uVar8;
  int iVar9;
  uint uVar10;
  
  while( true ) {
    uVar7 = *param_1;
    uVar8 = *param_2;
    uVar1 = UnsignedSaturate(1 - (uVar7 & 0xff),8);
    uVar2 = UnsignedSaturate(1 - (uVar7 >> 8 & 0xff),8);
    uVar3 = UnsignedSaturate(1 - (uVar7 >> 0x10 & 0xff),8);
    uVar4 = UnsignedSaturate(1 - (uVar7 >> 0x18),8);
    iVar9 = CONCAT13((char)uVar4,CONCAT12((char)uVar3,CONCAT11((char)uVar2,(char)uVar1)));
    uVar10 = uVar7 - uVar8;
    if ((uVar10 != 0) || (iVar9 != 0)) break;
    uVar7 = param_1[1];
    uVar8 = param_2[1];
    uVar1 = UnsignedSaturate(1 - (uVar7 & 0xff),8);
    uVar2 = UnsignedSaturate(1 - (uVar7 >> 8 & 0xff),8);
    uVar3 = UnsignedSaturate(1 - (uVar7 >> 0x10 & 0xff),8);
    uVar4 = UnsignedSaturate(1 - (uVar7 >> 0x18),8);
    iVar9 = CONCAT13((char)uVar4,CONCAT12((char)uVar3,CONCAT11((char)uVar2,(char)uVar1)));
    uVar10 = uVar7 - uVar8;
    if ((uVar10 != 0) || (iVar9 != 0)) break;
    puVar5 = param_1 + 3;
    uVar7 = param_1[2];
    puVar6 = param_2 + 3;
    uVar8 = param_2[2];
    uVar1 = UnsignedSaturate(1 - (uVar7 & 0xff),8);
    uVar2 = UnsignedSaturate(1 - (uVar7 >> 8 & 0xff),8);
    uVar3 = UnsignedSaturate(1 - (uVar7 >> 0x10 & 0xff),8);
    uVar4 = UnsignedSaturate(1 - (uVar7 >> 0x18),8);
    iVar9 = CONCAT13((char)uVar4,CONCAT12((char)uVar3,CONCAT11((char)uVar2,(char)uVar1)));
    uVar10 = uVar7 - uVar8;
    if ((uVar10 != 0) || (iVar9 != 0)) break;
    param_1 = param_1 + 4;
    uVar7 = *puVar5;
    param_2 = param_2 + 4;
    uVar8 = *puVar6;
    uVar1 = UnsignedSaturate(1 - (uVar7 & 0xff),8);
    uVar2 = UnsignedSaturate(1 - (uVar7 >> 8 & 0xff),8);
    uVar3 = UnsignedSaturate(1 - (uVar7 >> 0x10 & 0xff),8);
    uVar4 = UnsignedSaturate(1 - (uVar7 >> 0x18),8);
    iVar9 = CONCAT13((char)uVar4,CONCAT12((char)uVar3,CONCAT11((char)uVar2,(char)uVar1)));
    uVar10 = uVar7 - uVar8;
    if (uVar10 != 0) break;
    if (iVar9 != 0) {
      return 0;
    }
  }
  uVar10 = LZCOUNT(uVar10 << 0x18 | (uVar10 >> 8 & 0xff) << 0x10 | (uVar10 >> 0x10 & 0xff) << 8 |
                   uVar10 >> 0x18) & 0x18;
  if (iVar9 << (0x20 - uVar10 & 0xff) != 0) {
    return 0;
  }
  return (uVar7 >> uVar10 & 0xff) - (uVar8 >> uVar10 & 0xff);
}



/* 0800085c */

undefined4 FUN_0800085c(void)

{
  return DAT_08000860;
}



/* 0800086c */

/* WARNING: Removing unreachable block (ram,0x08000880) */

longlong FUN_0800086c(void)

{
  undefined1 local_10 [4];
  
  return ZEXT48(local_10) << 0x20;
}



/* 08000894 */

void FUN_08000894(uint param_1,uint param_2,undefined4 param_3,uint param_4)

{
  uint *puVar1;
  uint uVar2;
  bool bVar3;
  uint local_18;
  
  local_18 = param_4;
  if ((param_2 < param_1 + 0xc) &&
     (FUN_08000e10(0,&local_18,0xc), bVar3 = local_18 != param_2, param_2 = local_18, bVar3)) {
    param_1 = local_18;
  }
  puVar1 = (uint *)FUN_0800085c();
  *puVar1 = param_1;
  uVar2 = param_1 + 0x10;
  FUN_08000ab4(param_1);
  if (param_2 == uVar2) {
    return;
  }
  FUN_08000ac0(*puVar1,uVar2,param_2 - uVar2,local_18);
  return;
}



/* 080008f2 */

uint * FUN_080008f2(uint param_1)

{
  uint *puVar1;
  uint *puVar2;
  undefined4 *puVar3;
  int *piVar4;
  int iVar5;
  uint uVar6;
  uint *puVar7;
  
  puVar3 = (undefined4 *)FUN_0800085c();
  puVar7 = (uint *)*puVar3;
  uVar6 = param_1 + 0xb & 0xfffffff8;
  if (uVar6 <= param_1) {
    return (uint *)0x0;
  }
  do {
    puVar1 = puVar7;
    for (puVar2 = (uint *)puVar7[1]; puVar2 != (uint *)0x0; puVar2 = (uint *)puVar2[1]) {
      if (uVar6 <= *puVar2) {
        if (*puVar2 < uVar6 + 8) {
          puVar1[1] = puVar2[1];
        }
        else {
          piVar4 = (int *)((int)puVar2 + uVar6);
          piVar4[1] = puVar2[1];
          *piVar4 = *puVar2 - uVar6;
          puVar1[1] = (uint)piVar4;
          *puVar2 = uVar6;
        }
        return puVar2 + 1;
      }
      puVar1 = puVar2;
    }
    iVar5 = FUN_0800086c(puVar7,uVar6);
  } while (iVar5 != 0);
  return (uint *)0x0;
}



/* 08000a0e */

void FUN_08000a0e(undefined4 param_1,undefined4 param_2,undefined4 param_3,undefined4 param_4)

{
  undefined1 auStack_40 [4];
  undefined4 local_3c;
  undefined4 uStack_38;
  int local_34;
  undefined4 uStack_30;
  undefined4 local_2c;
  
  local_2c = 0;
  local_34 = DAT_08000a30 + 0x8000a20;
  local_3c = param_4;
  uStack_38 = param_2;
  uStack_30 = param_1;
  FUN_08000508(auStack_40,param_3);
  return;
}



/* 08000a34 */

void FUN_08000a34(undefined1 param_1,undefined4 *param_2)

{
  undefined1 *puVar1;
  
  puVar1 = (undefined1 *)*param_2;
  *puVar1 = param_1;
  *param_2 = puVar1 + 1;
  return;
}



/* 08000aa4 */

undefined4 FUN_08000aa4(void)

{
  return DAT_08000aa8;
}



/* 08000aac */

undefined4 FUN_08000aac(void)

{
  return DAT_08000ab0;
}



/* 08000ab4 */

void FUN_08000ab4(undefined4 *param_1)

{
  *param_1 = 0;
  param_1[1] = 0;
  return;
}



/* 08000ac0 */

void FUN_08000ac0(int *param_1,int *param_2,int param_3)

{
  int *piVar1;
  
  piVar1 = (int *)param_1[1];
  for (; piVar1 != (int *)0x0 && piVar1 < param_2; piVar1 = (int *)piVar1[1]) {
    param_1 = piVar1;
  }
  piVar1 = param_2;
  if ((int *)(*param_1 + (int)param_1) != param_2) {
    piVar1 = (int *)(((int)param_2 + 3U & 0xfffffff8) + 4);
    param_3 = param_3 - ((int)piVar1 - (int)param_2);
  }
  *piVar1 = param_3;
  FUN_080002d8(piVar1 + 1);
  return;
}



/* 08000cd8 */

void FUN_08000cd8(void)

{
  int iVar1;
  int iVar2;
  int *piVar3;
  int iVar4;
  
  FUN_08000788(DAT_08000de4,0x54);
  FUN_08000788(DAT_08000de8,0x54);
  FUN_08000788(DAT_08000dec,0x54);
  piVar3 = DAT_08000df8;
  iVar1 = DAT_08000de8;
  iVar4 = DAT_08000de4;
  *DAT_08000df0 = DAT_08000de4;
  *DAT_08000df4 = iVar1;
  iVar2 = DAT_08000dec;
  *piVar3 = DAT_08000dec;
  *(int *)(iVar4 + 0x50) = iVar1 + 1;
  *(int *)(iVar1 + 0x50) = iVar2 + 1;
  *(undefined4 *)(iVar2 + 0x50) = 1;
  iVar4 = FUN_08000fb8(DAT_08000e00 + 0x8000d1a,&DAT_08000dfc,DAT_08000de4);
  if (iVar4 == 0) {
    FUN_08001110(DAT_08000e00 + 0x8000d1a);
  }
  iVar4 = FUN_08000fb8(DAT_08000e08 + 0x8000d32,&DAT_08000e04,DAT_08000de8);
  if (iVar4 == 0) {
    FUN_08001110(DAT_08000e08 + 0x8000d32);
  }
  iVar4 = FUN_08000fb8(DAT_08000e0c + 0x8000d4a,&DAT_08000e04,DAT_08000dec);
  if (iVar4 == 0) {
    FUN_08001110(DAT_08000e0c + 0x8000d4a);
  }
  iVar4 = FUN_08000e68(DAT_08000de4,0,0x200);
  if (iVar4 != 0) {
    FUN_08001110(DAT_08000e00 + 0x8000d1a);
  }
  iVar4 = FUN_08000e68(DAT_08000de8,0,0x200,0x40);
  if (iVar4 != 0) {
    FUN_08001110(DAT_08000e08 + 0x8000d32);
  }
  iVar4 = FUN_08000e68(DAT_08000dec,0,0x200,0x10);
  if (iVar4 != 0) {
    FUN_08001110(DAT_08000e0c + 0x8000d4a);
    return;
  }
  return;
}



/* 08000daa */

void FUN_08000daa(void)

{
  uint uVar1;
  uint uVar2;
  
  uVar1 = *(uint *)(DAT_08000dec + 0x50);
  FUN_080010a8(DAT_08000de4);
  FUN_080010a8(DAT_08000de8);
  FUN_080010a8(DAT_08000dec);
  while (uVar2 = uVar1 & 0xfffffffe, uVar2 != 0) {
    uVar1 = *(uint *)(uVar2 + 0x50);
    FUN_080010a8(uVar2);
    FUN_080002d8(uVar2);
  }
  return;
}



/* 08000e10 */

void FUN_08000e10(void)

{
  int iVar1;
  
  iVar1 = FUN_08001120();
  if (iVar1 != 0) {
    FUN_0800b630();
    return;
  }
  return;
}



/* 08000e1e */

void FUN_08000e1e(void)

{
  uint uVar1;
  undefined4 *puVar2;
  undefined4 unaff_lr;
  uint *puVar3;
  
  uVar1 = FUN_08000aa4();
  *(undefined4 *)((uVar1 & 0xfffffff8) + 0x5c) = unaff_lr;
  puVar3 = (uint *)((uVar1 & 0xfffffff8) + 0x58);
  *puVar3 = uVar1;
  FUN_08000288();
  puVar2 = (undefined4 *)*puVar3;
  *puVar2 = 0;
  puVar2[1] = 0;
  puVar2[2] = 0;
  puVar2[3] = 0;
  puVar2[4] = 0;
  puVar2[5] = 0;
  puVar2[6] = 0;
  puVar2[7] = 0;
  puVar2[8] = 0;
  puVar2[9] = 0;
  puVar2[10] = 0;
  puVar2[0xb] = 0;
  puVar2[0xc] = 0;
  puVar2[0xd] = 0;
  puVar2[0xe] = 0;
  puVar2[0xf] = 0;
  return;
}



/* 08000e68 */

undefined4 FUN_08000e68(int param_1,int param_2,uint param_3,int param_4)

{
  uint uVar1;
  
  uVar1 = *(uint *)(param_1 + 0xc);
  if (((uVar1 & 3) != 0) && (-1 < (int)(uVar1 << 9))) {
    if ((param_3 == 0x100) || (param_3 == 0x200)) {
      if (0xfffffe < param_4 - 1U) {
        return 1;
      }
    }
    else {
      if (param_3 != 0x400) {
        return 1;
      }
      param_4 = 1;
      param_2 = param_1 + 0x24;
    }
    *(int *)(param_1 + 0x10) = param_2;
    *(int *)(param_1 + 0x1c) = param_4;
    *(int *)(param_1 + 4) = param_2;
    *(uint *)(param_1 + 0xc) = uVar1 & 0xfffff0ff | param_3;
    return 0;
  }
  return 1;
}



/* 08000eb0 */

void FUN_08000eb0(undefined4 *param_1)

{
  param_1[3] = param_1[3] & 0xffdfffff | 0x80;
  param_1[2] = 0;
  *param_1 = 0;
  return;
}



/* 08000ec4 */

undefined8 FUN_08000ec4(undefined4 param_1,uint param_2,int param_3)

{
  int iVar1;
  uint uVar2;
  uint uVar3;
  uint uVar4;
  undefined4 uVar5;
  uint uVar6;
  int iVar7;
  
  uVar4 = *(uint *)(param_3 + 0xc);
  uVar5 = *(undefined4 *)(param_3 + 0x14);
  uVar6 = param_2;
  iVar7 = param_3;
  if ((uVar4 & DAT_08000fb4) != 0) {
    iVar1 = FUN_0800b6a8(uVar5,*(undefined4 *)(param_3 + 0x18));
    if (iVar1 < 0) {
LAB_08000f1c:
      FUN_08000eb0(param_3);
      uVar5 = 0xffffffff;
      goto LAB_08000f24;
    }
    uVar4 = uVar4 & ~DAT_08000fb4;
    *(uint *)(param_3 + 0xc) = uVar4;
  }
  do {
    uVar3 = param_2;
    if (0x7fffffff < param_2) {
      uVar3 = 0x7fffffff;
    }
    uVar2 = FUN_0800b6b0(uVar5,param_1,uVar3,uVar4,param_1,uVar6,iVar7);
    *(uint *)(param_3 + 0x18) = *(int *)(param_3 + 0x18) + (uVar3 - (uVar2 & 0x7fffffff));
    if (uVar2 != 0) goto LAB_08000f1c;
    param_2 = param_2 - uVar3;
  } while (param_2 != 0);
  uVar5 = 0;
LAB_08000f24:
  return CONCAT44(param_1,uVar5);
}



/* 08000f30 */

undefined4 FUN_08000f30(int param_1)

{
  uint uVar1;
  int iVar2;
  uint uVar3;
  uint uVar4;
  
  uVar4 = *(uint *)(param_1 + 0x10);
  uVar1 = *(uint *)(param_1 + 0x2c);
  if (*(uint *)(param_1 + 0x2c) <= *(uint *)(param_1 + 4)) {
    uVar1 = *(uint *)(param_1 + 4);
  }
  uVar3 = *(uint *)(param_1 + 0xc);
  *(uint *)(param_1 + 0xc) = uVar3 & 0xffd7ffff;
  if ((int)(uVar3 << 0xf) < 0) {
    if ((uVar1 != uVar4) && (iVar2 = FUN_08000ec4(uVar4,uVar1 - uVar4,param_1), iVar2 != 0)) {
      return 0xffffffff;
    }
    *(uint *)(param_1 + 0x2c) = uVar4;
    *(uint *)(param_1 + 4) = uVar4;
    *(undefined4 *)(param_1 + 8) = 0;
    *(uint *)(param_1 + 0xc) = *(uint *)(param_1 + 0xc) & 0xfffeffff;
  }
  return 0;
}



/* 08000f76 */

void FUN_08000f76(int param_1)

{
  *(uint *)(param_1 + 0xc) = *(uint *)(param_1 + 0xc) & 0xffffffdf;
  if (*(int *)(param_1 + 0x18) != *(int *)(param_1 + 0x28)) {
    FUN_08000f30(param_1);
    *(uint *)(param_1 + 0xc) = *(uint *)(param_1 + 0xc) & 0xffffcfff | 0x10;
    *(undefined4 *)(param_1 + 0x18) = *(undefined4 *)(param_1 + 0x28);
    *(undefined4 *)(param_1 + 0x2c) = *(undefined4 *)(param_1 + 0x10);
    *(undefined4 *)(param_1 + 4) = *(undefined4 *)(param_1 + 0x10);
  }
  *(uint *)(param_1 + 0xc) = *(uint *)(param_1 + 0xc) & 0xffffbfbf;
  return;
}



/* 08000fb8 */

int FUN_08000fb8(int param_1,char *param_2,int param_3)

{
  char cVar1;
  int iVar2;
  uint uVar3;
  uint uVar4;
  
  if (param_1 != 0) {
    FUN_080010a8(param_3);
    cVar1 = *param_2;
    param_2 = param_2 + 1;
    if (cVar1 == 'a') {
      uVar3 = 8;
      uVar4 = 0x8002;
    }
    else if (cVar1 == 'r') {
      uVar4 = 1;
      uVar3 = 0;
    }
    else {
      if (cVar1 != 'w') {
        return 0;
      }
      uVar4 = 2;
      uVar3 = 4;
    }
    while( true ) {
      while( true ) {
        if (*param_2 != '+') break;
        uVar4 = uVar4 | 3;
        uVar3 = uVar3 | 2;
        param_2 = param_2 + 1;
      }
      if (*param_2 != 'b') break;
      uVar4 = uVar4 | 4;
      uVar3 = uVar3 | 1;
      param_2 = param_2 + 1;
    }
    if (*param_2 == 't') {
      uVar3 = uVar3 | 0x10;
    }
    iVar2 = FUN_0800b648(param_1,uVar3);
    if (iVar2 != -1) {
      *(undefined4 *)(param_3 + 0x10) = 0;
      *(undefined4 *)(param_3 + 4) = 0;
      *(uint *)(param_3 + 0xc) = uVar4;
      *(undefined4 *)(param_3 + 0x1c) = 0x200;
      *(int *)(param_3 + 0x14) = iVar2;
      if ((int)(uVar3 << 0x1c) < 0) {
        FUN_08001170(param_3,0,2);
      }
      *(uint *)(param_3 + 0x50) = *(uint *)(param_3 + 0x50) | 1;
      return param_3;
    }
  }
  return 0;
}



/* 08001058 */

undefined4 FUN_08001058(undefined4 param_1,undefined4 param_2)

{
  uint uVar1;
  undefined4 uVar2;
  uint uVar3;
  
  uVar3 = DAT_080010a4;
  do {
    uVar1 = *(uint *)(uVar3 + 0x50);
    if ((uVar1 & 1) == 0) {
LAB_08001094:
      uVar2 = FUN_08000fb8(param_1,param_2,uVar3);
      return uVar2;
    }
    if (uVar1 >> 1 == 0) {
      uVar1 = FUN_080008f2(0x54);
      if (uVar1 == 0) {
        return 0;
      }
      *(uint *)(uVar3 + 0x50) = *(uint *)(uVar3 + 0x50) | uVar1 | 1;
      FUN_08000788(uVar1,0x54);
      uVar3 = uVar1;
      goto LAB_08001094;
    }
    uVar3 = uVar1 & 0xfffffffe;
  } while( true );
}



/* 080010a8 */

undefined4 FUN_080010a8(int param_1)

{
  int iVar1;
  uint uVar2;
  undefined4 uVar3;
  undefined4 uVar4;
  undefined4 uVar5;
  
  uVar3 = 0;
  uVar2 = *(uint *)(param_1 + 0xc);
  uVar5 = *(undefined4 *)(param_1 + 0x10);
  uVar4 = *(undefined4 *)(param_1 + 0x14);
  if ((uVar2 & 3) == 0) {
    uVar3 = 0xffffffff;
  }
  else {
    FUN_08000f30(param_1);
    iVar1 = FUN_0800b61c(uVar4);
    if (iVar1 < 0) {
      uVar3 = 0xffffffff;
    }
    if ((int)(uVar2 << 0x14) < 0) {
      FUN_080002d8(uVar5);
    }
    FUN_08000788(param_1,0x4c);
    *(uint *)(param_1 + 0x50) = *(uint *)(param_1 + 0x50) & 0xfffffffe;
  }
  return uVar3;
}



/* 080010f4 */

void FUN_080010f4(undefined4 param_1,undefined4 param_2)

{
  FUN_08000246();
  FUN_0800b630(param_1,param_2);
  (*DAT_08000294)();
                    /* WARNING: Could not recover jumptable at 0x08000272. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*DAT_08000298)();
  return;
}



/* 08001110 */

void FUN_08001110(void)

{
  int iVar1;
  
  iVar1 = FUN_0800129c();
  if (iVar1 != 0) {
    FUN_0800b630();
    return;
  }
  return;
}



/* 08001120 */

undefined4 FUN_08001120(int param_1)

{
  char *pcVar1;
  
  if (param_1 == 1) {
    pcVar1 = s___Heap_memory_corrupted_08001158;
  }
  else {
    pcVar1 = (char *)0x0;
  }
  FUN_08001268(s_SIGRTMEM__Out_of_heap_memory_08001138,pcVar1);
  return 1;
}



/* 08001170 */

undefined4 FUN_08001170(int *param_1,int param_2,int param_3)

{
  int iVar1;
  uint uVar2;
  uint uVar3;
  uint uVar4;
  uint uVar5;
  uint uVar6;
  int iVar7;
  
  iVar7 = param_1[5];
  if (((*(byte *)(param_1 + 3) & 3) == 0) || (iVar1 = FUN_0800b638(iVar7), iVar1 != 0)) {
    return 2;
  }
  if (param_3 != 0) {
    if (param_3 == 1) {
      iVar7 = FUN_080012d0(param_1);
      param_2 = param_2 + iVar7;
    }
    else {
      if (param_3 != 2) {
        return 2;
      }
      iVar7 = FUN_0800b634(iVar7);
      uVar2 = param_1[3];
      param_1[3] = uVar2 | 0x10;
      if (iVar7 < 0) {
        FUN_08000eb0(param_1);
        return 1;
      }
      if ((int)((uVar2 | 0x10) << 0xf) < 0) {
        uVar2 = param_1[0xb];
        if ((uint)param_1[0xb] <= (uint)param_1[1]) {
          uVar2 = param_1[1];
        }
        iVar1 = (uVar2 + param_1[6]) - param_1[4];
        if (iVar7 < iVar1) {
          iVar7 = iVar1;
        }
      }
      param_2 = param_2 + iVar7;
    }
  }
  if (param_2 < 0) {
    return 2;
  }
  uVar2 = param_1[1];
  uVar4 = param_1[3];
  if (((uint)param_1[0xb] < uVar2) && (param_1[0xb] = uVar2, (int)(uVar4 << 0xe) < 0)) {
    uVar4 = uVar4 & 0xfffdffff | 0x10;
  }
  iVar7 = param_1[6];
  if (iVar7 <= param_2) {
    uVar3 = param_1[0xb];
    uVar5 = uVar2;
    if (uVar2 < uVar3) {
      uVar5 = uVar3;
    }
    uVar6 = param_1[4];
    if (param_2 < (int)((uVar5 + iVar7) - uVar6)) {
      uVar5 = uVar2;
      if (uVar2 < uVar3) {
        uVar5 = uVar3;
      }
      if (uVar5 != uVar6) {
        param_2 = param_2 - iVar7;
        param_1[2] = param_2 - param_1[7];
        if (uVar2 < uVar3) {
          uVar2 = uVar3;
        }
        *param_1 = param_2 - (uVar2 - uVar6);
        param_1[1] = uVar6 + param_2;
        uVar4 = uVar4 & 0xffffffdf;
        goto LAB_08001254;
      }
    }
  }
  param_1[2] = 0;
  *param_1 = 0;
  uVar4 = uVar4 | 0x20;
  param_1[10] = param_2;
LAB_08001254:
  param_1[3] = uVar4 & DAT_08001264;
  *(undefined1 *)(param_1 + 0x12) = 0;
  return 0;
}



/* 08001268 */

void FUN_08001268(char *param_1,char *param_2)

{
  char cVar1;
  
  cVar1 = '\n';
  for (; (thunk_FUN_0800fd6c(cVar1), param_1 != (char *)0x0 && (cVar1 = *param_1, cVar1 != '\0'));
      param_1 = param_1 + 1) {
  }
  for (; (param_2 != (char *)0x0 && (*param_2 != '\0')); param_2 = param_2 + 1) {
    thunk_FUN_0800fd6c();
  }
  thunk_FUN_0800fd6c(10);
  return;
}



/* 0800129c */

undefined4 FUN_0800129c(undefined4 param_1)

{
  FUN_08001268(s_SIGRTRED__Redirect__can_t_open__080012ac,param_1);
  return 1;
}



/* 080012d0 */

int FUN_080012d0(int param_1)

{
  int iVar1;
  undefined4 *puVar2;
  uint uVar3;
  
  uVar3 = *(uint *)(param_1 + 0xc);
  if ((uVar3 & 3) == 0) {
    puVar2 = (undefined4 *)FUN_08000aac();
    *puVar2 = 1;
    return -1;
  }
  if ((int)(uVar3 << 0x1a) < 0) {
    iVar1 = *(int *)(param_1 + 0x28);
  }
  else {
    iVar1 = (*(int *)(param_1 + 4) + *(int *)(param_1 + 0x18)) - *(int *)(param_1 + 0x10);
  }
  if (*(char *)(param_1 + 0x48) == '\0') {
    if (((int)(uVar3 << 0xc) < 0) && (0 < iVar1)) {
      return iVar1 + -1;
    }
  }
  else {
    iVar1 = iVar1 - (uint)*(byte *)(param_1 + 0x49);
  }
  return iVar1;
}



/* 080013a0 */

void BusFault_Handler(void)

{
  do {
                    /* WARNING: Do nothing block with infinite loop */
  } while( true );
}



/* 080013a4 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void IRQ_11_Handler(void)

{
  uint *puVar1;
  uint *puVar2;
  code *UNRECOVERED_JUMPTABLE;
  uint uVar3;
  uint uVar4;
  uint uVar5;
  uint uVar6;
  uint uStack_18;
  
  uVar4 = uRam2001d0b8;
  puVar2 = puRam2001d0b4;
  uVar5 = _DAT_2001c064;
  uStack_18 = 0;
  uVar6 = *puRam2001d0b4;
  uVar3 = 8 << (uRam2001d0b8 & 0xff);
  if (((uVar3 & uVar6) != 0) && ((int)(*_DAT_2001d058 << 0x1d) < 0)) {
    *_DAT_2001d058 = *_DAT_2001d058 & 0xfffffffb;
    puVar2[2] = uVar3;
    uRam2001d0b0 = uRam2001d0b0 | 1;
  }
  uVar3 = 1 << (uVar4 & 0xff);
  if (((uVar3 & uVar6) != 0) && ((int)(_DAT_2001d058[5] << 0x18) < 0)) {
    puVar2[2] = uVar3;
    uRam2001d0b0 = uRam2001d0b0 | 2;
  }
  uVar3 = 4 << (uVar4 & 0xff);
  if (((uVar3 & uVar6) != 0) && ((int)(*_DAT_2001d058 << 0x1e) < 0)) {
    puVar2[2] = uVar3;
    uRam2001d0b0 = uRam2001d0b0 | 4;
  }
  puVar1 = _DAT_2001d058;
  uVar4 = 0x10 << (uVar4 & 0xff);
  if (((uVar4 & uVar6) != 0) && ((int)(*_DAT_2001d058 << 0x1c) < 0)) {
    puVar2[2] = uVar4;
    if ((int)(*puVar1 << 0xd) < 0) {
      UNRECOVERED_JUMPTABLE = pcRam2001d0a4;
      if (-1 < (int)(*puVar1 << 0xc)) goto joined_r0x08001aba;
    }
    else {
      if (-1 < (int)(*puVar1 << 0x17)) {
        *puVar1 = *puVar1 & 0xfffffff7;
      }
joined_r0x08001aba:
      UNRECOVERED_JUMPTABLE = pcRam2001d09c;
    }
    if (UNRECOVERED_JUMPTABLE != (code *)0x0) {
      (*UNRECOVERED_JUMPTABLE)();
    }
  }
  uVar4 = uRam2001d0b8;
  puVar1 = _DAT_2001d058;
  uVar3 = 0x20 << (uRam2001d0b8 & 0xff);
  if (((uVar3 & uVar6) != 0) && ((int)(*_DAT_2001d058 << 0x1b) < 0)) {
    puVar2[2] = uVar3;
    if (iRam2001d090 == 5) {
      *puVar1 = *puVar1 & 0xffffffe9;
      puVar1[5] = puVar1[5] & 0xffffff7f;
      if ((pcRam2001d09c != (code *)0x0) || (pcRam2001d0a4 != (code *)0x0)) {
        *puVar1 = *puVar1 & 0xfffffff7;
      }
      puVar2[2] = 0x3f << (uVar4 & 0xff);
      iRam2001d090 = 1;
      uRam2001d08c = 0;
      UNRECOVERED_JUMPTABLE = pcRam2001d0ac;
      goto joined_r0x08001b10;
    }
    if ((int)(*puVar1 << 0xd) < 0) {
      UNRECOVERED_JUMPTABLE = pcRam2001d0a0;
      if ((int)(*puVar1 << 0xc) < 0) goto LAB_08001b40;
    }
    else {
      if (-1 < (int)(*puVar1 << 0x17)) {
        *puVar1 = *puVar1 & 0xffffffef;
        iRam2001d090 = 1;
        uRam2001d08c = 0;
      }
LAB_08001b40:
      UNRECOVERED_JUMPTABLE = pcRam2001d098;
    }
    if (UNRECOVERED_JUMPTABLE != (code *)0x0) {
      (*UNRECOVERED_JUMPTABLE)();
    }
  }
  puVar2 = _DAT_2001d058;
  if (uRam2001d0b0 == 0) {
    return;
  }
  UNRECOVERED_JUMPTABLE = pcRam2001d0a8;
  if ((uRam2001d0b0 & 1) != 0) {
    uVar5 = uVar5 / 0x2580;
    *_DAT_2001d058 = *_DAT_2001d058 & 0xfffffffe;
    while ((((uStack_18 + 1 <= uVar5 && ((*puVar2 & 1) != 0)) && (uStack_18 + 2 <= uVar5)) &&
           (((*puVar2 & 1) != 0 && (uStack_18 + 3 <= uVar5))))) {
      if (((*puVar2 & 1) == 0) ||
         ((uStack_18 = uStack_18 + 4, uVar5 < uStack_18 || ((*puVar2 & 1) == 0)))) break;
    }
    iRam2001d090 = 1;
    uRam2001d08c = 0;
    UNRECOVERED_JUMPTABLE = pcRam2001d0a8;
  }
joined_r0x08001b10:
  if (UNRECOVERED_JUMPTABLE == (code *)0x0) {
    return;
  }
                    /* WARNING: Could not recover jumptable at 0x08001bb6. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*UNRECOVERED_JUMPTABLE)();
  return;
}



/* 080013b0 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void IRQ_12_Handler(void)

{
  uint *puVar1;
  uint *puVar2;
  code *UNRECOVERED_JUMPTABLE;
  uint uVar3;
  uint uVar4;
  uint uVar5;
  uint uVar6;
  uint uStack_18;
  
  uVar4 = uRam2001d1e4;
  puVar2 = puRam2001d1e0;
  uVar5 = _DAT_2001c064;
  uStack_18 = 0;
  uVar6 = *puRam2001d1e0;
  uVar3 = 8 << (uRam2001d1e4 & 0xff);
  if (((uVar3 & uVar6) != 0) && ((int)(*_DAT_2001d184 << 0x1d) < 0)) {
    *_DAT_2001d184 = *_DAT_2001d184 & 0xfffffffb;
    puVar2[2] = uVar3;
    uRam2001d1dc = uRam2001d1dc | 1;
  }
  uVar3 = 1 << (uVar4 & 0xff);
  if (((uVar3 & uVar6) != 0) && ((int)(_DAT_2001d184[5] << 0x18) < 0)) {
    puVar2[2] = uVar3;
    uRam2001d1dc = uRam2001d1dc | 2;
  }
  uVar3 = 4 << (uVar4 & 0xff);
  if (((uVar3 & uVar6) != 0) && ((int)(*_DAT_2001d184 << 0x1e) < 0)) {
    puVar2[2] = uVar3;
    uRam2001d1dc = uRam2001d1dc | 4;
  }
  puVar1 = _DAT_2001d184;
  uVar4 = 0x10 << (uVar4 & 0xff);
  if (((uVar4 & uVar6) != 0) && ((int)(*_DAT_2001d184 << 0x1c) < 0)) {
    puVar2[2] = uVar4;
    if ((int)(*puVar1 << 0xd) < 0) {
      UNRECOVERED_JUMPTABLE = pcRam2001d1d0;
      if (-1 < (int)(*puVar1 << 0xc)) goto joined_r0x08001aba;
    }
    else {
      if (-1 < (int)(*puVar1 << 0x17)) {
        *puVar1 = *puVar1 & 0xfffffff7;
      }
joined_r0x08001aba:
      UNRECOVERED_JUMPTABLE = pcRam2001d1c8;
    }
    if (UNRECOVERED_JUMPTABLE != (code *)0x0) {
      (*UNRECOVERED_JUMPTABLE)();
    }
  }
  uVar4 = uRam2001d1e4;
  puVar1 = _DAT_2001d184;
  uVar3 = 0x20 << (uRam2001d1e4 & 0xff);
  if (((uVar3 & uVar6) != 0) && ((int)(*_DAT_2001d184 << 0x1b) < 0)) {
    puVar2[2] = uVar3;
    if (iRam2001d1bc == 5) {
      *puVar1 = *puVar1 & 0xffffffe9;
      puVar1[5] = puVar1[5] & 0xffffff7f;
      if ((pcRam2001d1c8 != (code *)0x0) || (pcRam2001d1d0 != (code *)0x0)) {
        *puVar1 = *puVar1 & 0xfffffff7;
      }
      puVar2[2] = 0x3f << (uVar4 & 0xff);
      iRam2001d1bc = 1;
      uRam2001d1b8 = 0;
      UNRECOVERED_JUMPTABLE = pcRam2001d1d8;
      goto joined_r0x08001b10;
    }
    if ((int)(*puVar1 << 0xd) < 0) {
      UNRECOVERED_JUMPTABLE = pcRam2001d1cc;
      if ((int)(*puVar1 << 0xc) < 0) goto LAB_08001b40;
    }
    else {
      if (-1 < (int)(*puVar1 << 0x17)) {
        *puVar1 = *puVar1 & 0xffffffef;
        iRam2001d1bc = 1;
        uRam2001d1b8 = 0;
      }
LAB_08001b40:
      UNRECOVERED_JUMPTABLE = pcRam2001d1c4;
    }
    if (UNRECOVERED_JUMPTABLE != (code *)0x0) {
      (*UNRECOVERED_JUMPTABLE)();
    }
  }
  puVar2 = _DAT_2001d184;
  if (uRam2001d1dc == 0) {
    return;
  }
  UNRECOVERED_JUMPTABLE = pcRam2001d1d4;
  if ((uRam2001d1dc & 1) != 0) {
    uVar5 = uVar5 / 0x2580;
    *_DAT_2001d184 = *_DAT_2001d184 & 0xfffffffe;
    while ((((uStack_18 + 1 <= uVar5 && ((*puVar2 & 1) != 0)) && (uStack_18 + 2 <= uVar5)) &&
           (((*puVar2 & 1) != 0 && (uStack_18 + 3 <= uVar5))))) {
      if (((*puVar2 & 1) == 0) ||
         ((uStack_18 = uStack_18 + 4, uVar5 < uStack_18 || ((*puVar2 & 1) == 0)))) break;
    }
    iRam2001d1bc = 1;
    uRam2001d1b8 = 0;
    UNRECOVERED_JUMPTABLE = pcRam2001d1d4;
  }
joined_r0x08001b10:
  if (UNRECOVERED_JUMPTABLE == (code *)0x0) {
    return;
  }
                    /* WARNING: Could not recover jumptable at 0x08001bb6. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*UNRECOVERED_JUMPTABLE)();
  return;
}



/* 080013bc */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void IRQ_14_Handler(void)

{
  uint *puVar1;
  uint *puVar2;
  code *UNRECOVERED_JUMPTABLE;
  uint uVar3;
  uint uVar4;
  uint uVar5;
  uint uVar6;
  uint uStack_18;
  
  uVar4 = uRam2001d248;
  puVar2 = puRam2001d244;
  uVar5 = _DAT_2001c064;
  uStack_18 = 0;
  uVar6 = *puRam2001d244;
  uVar3 = 8 << (uRam2001d248 & 0xff);
  if (((uVar3 & uVar6) != 0) && ((int)(*_DAT_2001d1e8 << 0x1d) < 0)) {
    *_DAT_2001d1e8 = *_DAT_2001d1e8 & 0xfffffffb;
    puVar2[2] = uVar3;
    uRam2001d240 = uRam2001d240 | 1;
  }
  uVar3 = 1 << (uVar4 & 0xff);
  if (((uVar3 & uVar6) != 0) && ((int)(_DAT_2001d1e8[5] << 0x18) < 0)) {
    puVar2[2] = uVar3;
    uRam2001d240 = uRam2001d240 | 2;
  }
  uVar3 = 4 << (uVar4 & 0xff);
  if (((uVar3 & uVar6) != 0) && ((int)(*_DAT_2001d1e8 << 0x1e) < 0)) {
    puVar2[2] = uVar3;
    uRam2001d240 = uRam2001d240 | 4;
  }
  puVar1 = _DAT_2001d1e8;
  uVar4 = 0x10 << (uVar4 & 0xff);
  if (((uVar4 & uVar6) != 0) && ((int)(*_DAT_2001d1e8 << 0x1c) < 0)) {
    puVar2[2] = uVar4;
    if ((int)(*puVar1 << 0xd) < 0) {
      UNRECOVERED_JUMPTABLE = pcRam2001d234;
      if (-1 < (int)(*puVar1 << 0xc)) goto joined_r0x08001aba;
    }
    else {
      if (-1 < (int)(*puVar1 << 0x17)) {
        *puVar1 = *puVar1 & 0xfffffff7;
      }
joined_r0x08001aba:
      UNRECOVERED_JUMPTABLE = pcRam2001d22c;
    }
    if (UNRECOVERED_JUMPTABLE != (code *)0x0) {
      (*UNRECOVERED_JUMPTABLE)();
    }
  }
  uVar4 = uRam2001d248;
  puVar1 = _DAT_2001d1e8;
  uVar3 = 0x20 << (uRam2001d248 & 0xff);
  if (((uVar3 & uVar6) != 0) && ((int)(*_DAT_2001d1e8 << 0x1b) < 0)) {
    puVar2[2] = uVar3;
    if (iRam2001d220 == 5) {
      *puVar1 = *puVar1 & 0xffffffe9;
      puVar1[5] = puVar1[5] & 0xffffff7f;
      if ((pcRam2001d22c != (code *)0x0) || (pcRam2001d234 != (code *)0x0)) {
        *puVar1 = *puVar1 & 0xfffffff7;
      }
      puVar2[2] = 0x3f << (uVar4 & 0xff);
      iRam2001d220 = 1;
      uRam2001d21c = 0;
      UNRECOVERED_JUMPTABLE = pcRam2001d23c;
      goto joined_r0x08001b10;
    }
    if ((int)(*puVar1 << 0xd) < 0) {
      UNRECOVERED_JUMPTABLE = pcRam2001d230;
      if ((int)(*puVar1 << 0xc) < 0) goto LAB_08001b40;
    }
    else {
      if (-1 < (int)(*puVar1 << 0x17)) {
        *puVar1 = *puVar1 & 0xffffffef;
        iRam2001d220 = 1;
        uRam2001d21c = 0;
      }
LAB_08001b40:
      UNRECOVERED_JUMPTABLE = pcRam2001d228;
    }
    if (UNRECOVERED_JUMPTABLE != (code *)0x0) {
      (*UNRECOVERED_JUMPTABLE)();
    }
  }
  puVar2 = _DAT_2001d1e8;
  if (uRam2001d240 == 0) {
    return;
  }
  UNRECOVERED_JUMPTABLE = pcRam2001d238;
  if ((uRam2001d240 & 1) != 0) {
    uVar5 = uVar5 / 0x2580;
    *_DAT_2001d1e8 = *_DAT_2001d1e8 & 0xfffffffe;
    while ((((uStack_18 + 1 <= uVar5 && ((*puVar2 & 1) != 0)) && (uStack_18 + 2 <= uVar5)) &&
           (((*puVar2 & 1) != 0 && (uStack_18 + 3 <= uVar5))))) {
      if (((*puVar2 & 1) == 0) ||
         ((uStack_18 = uStack_18 + 4, uVar5 < uStack_18 || ((*puVar2 & 1) == 0)))) break;
    }
    iRam2001d220 = 1;
    uRam2001d21c = 0;
    UNRECOVERED_JUMPTABLE = pcRam2001d238;
  }
joined_r0x08001b10:
  if (UNRECOVERED_JUMPTABLE == (code *)0x0) {
    return;
  }
                    /* WARNING: Could not recover jumptable at 0x08001bb6. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*UNRECOVERED_JUMPTABLE)();
  return;
}



/* 080013c8 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void IRQ_15_Handler(void)

{
  uint *puVar1;
  uint *puVar2;
  code *UNRECOVERED_JUMPTABLE;
  uint uVar3;
  uint uVar4;
  uint uVar5;
  uint uVar6;
  uint uStack_18;
  
  uVar4 = uRam2001d054;
  puVar2 = puRam2001d050;
  uVar5 = _DAT_2001c064;
  uStack_18 = 0;
  uVar6 = *puRam2001d050;
  uVar3 = 8 << (uRam2001d054 & 0xff);
  if (((uVar3 & uVar6) != 0) && ((int)(*_DAT_2001cff4 << 0x1d) < 0)) {
    *_DAT_2001cff4 = *_DAT_2001cff4 & 0xfffffffb;
    puVar2[2] = uVar3;
    uRam2001d04c = uRam2001d04c | 1;
  }
  uVar3 = 1 << (uVar4 & 0xff);
  if (((uVar3 & uVar6) != 0) && ((int)(_DAT_2001cff4[5] << 0x18) < 0)) {
    puVar2[2] = uVar3;
    uRam2001d04c = uRam2001d04c | 2;
  }
  uVar3 = 4 << (uVar4 & 0xff);
  if (((uVar3 & uVar6) != 0) && ((int)(*_DAT_2001cff4 << 0x1e) < 0)) {
    puVar2[2] = uVar3;
    uRam2001d04c = uRam2001d04c | 4;
  }
  puVar1 = _DAT_2001cff4;
  uVar4 = 0x10 << (uVar4 & 0xff);
  if (((uVar4 & uVar6) != 0) && ((int)(*_DAT_2001cff4 << 0x1c) < 0)) {
    puVar2[2] = uVar4;
    if ((int)(*puVar1 << 0xd) < 0) {
      UNRECOVERED_JUMPTABLE = pcRam2001d040;
      if (-1 < (int)(*puVar1 << 0xc)) goto joined_r0x08001aba;
    }
    else {
      if (-1 < (int)(*puVar1 << 0x17)) {
        *puVar1 = *puVar1 & 0xfffffff7;
      }
joined_r0x08001aba:
      UNRECOVERED_JUMPTABLE = pcRam2001d038;
    }
    if (UNRECOVERED_JUMPTABLE != (code *)0x0) {
      (*UNRECOVERED_JUMPTABLE)();
    }
  }
  uVar4 = uRam2001d054;
  puVar1 = _DAT_2001cff4;
  uVar3 = 0x20 << (uRam2001d054 & 0xff);
  if (((uVar3 & uVar6) != 0) && ((int)(*_DAT_2001cff4 << 0x1b) < 0)) {
    puVar2[2] = uVar3;
    if (iRam2001d02c == 5) {
      *puVar1 = *puVar1 & 0xffffffe9;
      puVar1[5] = puVar1[5] & 0xffffff7f;
      if ((pcRam2001d038 != (code *)0x0) || (pcRam2001d040 != (code *)0x0)) {
        *puVar1 = *puVar1 & 0xfffffff7;
      }
      puVar2[2] = 0x3f << (uVar4 & 0xff);
      iRam2001d02c = 1;
      uRam2001d028 = 0;
      UNRECOVERED_JUMPTABLE = pcRam2001d048;
      goto joined_r0x08001b10;
    }
    if ((int)(*puVar1 << 0xd) < 0) {
      UNRECOVERED_JUMPTABLE = pcRam2001d03c;
      if ((int)(*puVar1 << 0xc) < 0) goto LAB_08001b40;
    }
    else {
      if (-1 < (int)(*puVar1 << 0x17)) {
        *puVar1 = *puVar1 & 0xffffffef;
        iRam2001d02c = 1;
        uRam2001d028 = 0;
      }
LAB_08001b40:
      UNRECOVERED_JUMPTABLE = pcRam2001d034;
    }
    if (UNRECOVERED_JUMPTABLE != (code *)0x0) {
      (*UNRECOVERED_JUMPTABLE)();
    }
  }
  puVar2 = _DAT_2001cff4;
  if (uRam2001d04c == 0) {
    return;
  }
  UNRECOVERED_JUMPTABLE = pcRam2001d044;
  if ((uRam2001d04c & 1) != 0) {
    uVar5 = uVar5 / 0x2580;
    *_DAT_2001cff4 = *_DAT_2001cff4 & 0xfffffffe;
    while ((((uStack_18 + 1 <= uVar5 && ((*puVar2 & 1) != 0)) && (uStack_18 + 2 <= uVar5)) &&
           (((*puVar2 & 1) != 0 && (uStack_18 + 3 <= uVar5))))) {
      if (((*puVar2 & 1) == 0) ||
         ((uStack_18 = uStack_18 + 4, uVar5 < uStack_18 || ((*puVar2 & 1) == 0)))) break;
    }
    iRam2001d02c = 1;
    uRam2001d028 = 0;
    UNRECOVERED_JUMPTABLE = pcRam2001d044;
  }
joined_r0x08001b10:
  if (UNRECOVERED_JUMPTABLE == (code *)0x0) {
    return;
  }
                    /* WARNING: Could not recover jumptable at 0x08001bb6. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*UNRECOVERED_JUMPTABLE)();
  return;
}



/* 080013d4 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void IRQ_16_Handler(void)

{
  uint *puVar1;
  uint *puVar2;
  code *UNRECOVERED_JUMPTABLE;
  uint uVar3;
  uint uVar4;
  uint uVar5;
  uint uVar6;
  uint uStack_18;
  
  uVar4 = uRam2001d11c;
  puVar2 = puRam2001d118;
  uVar5 = _DAT_2001c064;
  uStack_18 = 0;
  uVar6 = *puRam2001d118;
  uVar3 = 8 << (uRam2001d11c & 0xff);
  if (((uVar3 & uVar6) != 0) && ((int)(*_DAT_2001d0bc << 0x1d) < 0)) {
    *_DAT_2001d0bc = *_DAT_2001d0bc & 0xfffffffb;
    puVar2[2] = uVar3;
    uRam2001d114 = uRam2001d114 | 1;
  }
  uVar3 = 1 << (uVar4 & 0xff);
  if (((uVar3 & uVar6) != 0) && ((int)(_DAT_2001d0bc[5] << 0x18) < 0)) {
    puVar2[2] = uVar3;
    uRam2001d114 = uRam2001d114 | 2;
  }
  uVar3 = 4 << (uVar4 & 0xff);
  if (((uVar3 & uVar6) != 0) && ((int)(*_DAT_2001d0bc << 0x1e) < 0)) {
    puVar2[2] = uVar3;
    uRam2001d114 = uRam2001d114 | 4;
  }
  puVar1 = _DAT_2001d0bc;
  uVar4 = 0x10 << (uVar4 & 0xff);
  if (((uVar4 & uVar6) != 0) && ((int)(*_DAT_2001d0bc << 0x1c) < 0)) {
    puVar2[2] = uVar4;
    if ((int)(*puVar1 << 0xd) < 0) {
      UNRECOVERED_JUMPTABLE = pcRam2001d108;
      if (-1 < (int)(*puVar1 << 0xc)) goto joined_r0x08001aba;
    }
    else {
      if (-1 < (int)(*puVar1 << 0x17)) {
        *puVar1 = *puVar1 & 0xfffffff7;
      }
joined_r0x08001aba:
      UNRECOVERED_JUMPTABLE = pcRam2001d100;
    }
    if (UNRECOVERED_JUMPTABLE != (code *)0x0) {
      (*UNRECOVERED_JUMPTABLE)();
    }
  }
  uVar4 = uRam2001d11c;
  puVar1 = _DAT_2001d0bc;
  uVar3 = 0x20 << (uRam2001d11c & 0xff);
  if (((uVar3 & uVar6) != 0) && ((int)(*_DAT_2001d0bc << 0x1b) < 0)) {
    puVar2[2] = uVar3;
    if (iRam2001d0f4 == 5) {
      *puVar1 = *puVar1 & 0xffffffe9;
      puVar1[5] = puVar1[5] & 0xffffff7f;
      if ((pcRam2001d100 != (code *)0x0) || (pcRam2001d108 != (code *)0x0)) {
        *puVar1 = *puVar1 & 0xfffffff7;
      }
      puVar2[2] = 0x3f << (uVar4 & 0xff);
      iRam2001d0f4 = 1;
      uRam2001d0f0 = 0;
      UNRECOVERED_JUMPTABLE = pcRam2001d110;
      goto joined_r0x08001b10;
    }
    if ((int)(*puVar1 << 0xd) < 0) {
      UNRECOVERED_JUMPTABLE = pcRam2001d104;
      if ((int)(*puVar1 << 0xc) < 0) goto LAB_08001b40;
    }
    else {
      if (-1 < (int)(*puVar1 << 0x17)) {
        *puVar1 = *puVar1 & 0xffffffef;
        iRam2001d0f4 = 1;
        uRam2001d0f0 = 0;
      }
LAB_08001b40:
      UNRECOVERED_JUMPTABLE = pcRam2001d0fc;
    }
    if (UNRECOVERED_JUMPTABLE != (code *)0x0) {
      (*UNRECOVERED_JUMPTABLE)();
    }
  }
  puVar2 = _DAT_2001d0bc;
  if (uRam2001d114 == 0) {
    return;
  }
  UNRECOVERED_JUMPTABLE = pcRam2001d10c;
  if ((uRam2001d114 & 1) != 0) {
    uVar5 = uVar5 / 0x2580;
    *_DAT_2001d0bc = *_DAT_2001d0bc & 0xfffffffe;
    while ((((uStack_18 + 1 <= uVar5 && ((*puVar2 & 1) != 0)) && (uStack_18 + 2 <= uVar5)) &&
           (((*puVar2 & 1) != 0 && (uStack_18 + 3 <= uVar5))))) {
      if (((*puVar2 & 1) == 0) ||
         ((uStack_18 = uStack_18 + 4, uVar5 < uStack_18 || ((*puVar2 & 1) == 0)))) break;
    }
    iRam2001d0f4 = 1;
    uRam2001d0f0 = 0;
    UNRECOVERED_JUMPTABLE = pcRam2001d10c;
  }
joined_r0x08001b10:
  if (UNRECOVERED_JUMPTABLE == (code *)0x0) {
    return;
  }
                    /* WARNING: Could not recover jumptable at 0x08001bb6. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*UNRECOVERED_JUMPTABLE)();
  return;
}



/* 080013e0 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void IRQ_17_Handler(void)

{
  uint *puVar1;
  uint *puVar2;
  code *UNRECOVERED_JUMPTABLE;
  uint uVar3;
  uint uVar4;
  uint uVar5;
  uint uVar6;
  uint local_18;
  
  uVar4 = _DAT_2001d180;
  puVar2 = _DAT_2001d17c;
  uVar5 = _DAT_2001c064;
  local_18 = 0;
  uVar6 = *_DAT_2001d17c;
  uVar3 = 8 << (_DAT_2001d180 & 0xff);
  if (((uVar3 & uVar6) != 0) && ((int)(*_DAT_2001d120 << 0x1d) < 0)) {
    *_DAT_2001d120 = *_DAT_2001d120 & 0xfffffffb;
    puVar2[2] = uVar3;
    _DAT_2001d178 = _DAT_2001d178 | 1;
  }
  uVar3 = 1 << (uVar4 & 0xff);
  if (((uVar3 & uVar6) != 0) && ((int)(_DAT_2001d120[5] << 0x18) < 0)) {
    puVar2[2] = uVar3;
    _DAT_2001d178 = _DAT_2001d178 | 2;
  }
  uVar3 = 4 << (uVar4 & 0xff);
  if (((uVar3 & uVar6) != 0) && ((int)(*_DAT_2001d120 << 0x1e) < 0)) {
    puVar2[2] = uVar3;
    _DAT_2001d178 = _DAT_2001d178 | 4;
  }
  puVar1 = _DAT_2001d120;
  uVar4 = 0x10 << (uVar4 & 0xff);
  if (((uVar4 & uVar6) != 0) && ((int)(*_DAT_2001d120 << 0x1c) < 0)) {
    puVar2[2] = uVar4;
    if ((int)(*puVar1 << 0xd) < 0) {
      UNRECOVERED_JUMPTABLE = _DAT_2001d16c;
      if (-1 < (int)(*puVar1 << 0xc)) goto joined_r0x08001aba;
    }
    else {
      if (-1 < (int)(*puVar1 << 0x17)) {
        *puVar1 = *puVar1 & 0xfffffff7;
      }
joined_r0x08001aba:
      UNRECOVERED_JUMPTABLE = _DAT_2001d164;
    }
    if (UNRECOVERED_JUMPTABLE != (code *)0x0) {
      (*UNRECOVERED_JUMPTABLE)();
    }
  }
  uVar4 = _DAT_2001d180;
  puVar1 = _DAT_2001d120;
  uVar3 = 0x20 << (_DAT_2001d180 & 0xff);
  if (((uVar3 & uVar6) != 0) && ((int)(*_DAT_2001d120 << 0x1b) < 0)) {
    puVar2[2] = uVar3;
    if (_DAT_2001d158 == 5) {
      *puVar1 = *puVar1 & 0xffffffe9;
      puVar1[5] = puVar1[5] & 0xffffff7f;
      if ((_DAT_2001d164 != (code *)0x0) || (_DAT_2001d16c != (code *)0x0)) {
        *puVar1 = *puVar1 & 0xfffffff7;
      }
      puVar2[2] = 0x3f << (uVar4 & 0xff);
      _DAT_2001d158 = 1;
      _DAT_2001d154 = 0;
      UNRECOVERED_JUMPTABLE = _DAT_2001d174;
      goto joined_r0x08001b10;
    }
    if ((int)(*puVar1 << 0xd) < 0) {
      UNRECOVERED_JUMPTABLE = _DAT_2001d168;
      if ((int)(*puVar1 << 0xc) < 0) goto LAB_08001b40;
    }
    else {
      if (-1 < (int)(*puVar1 << 0x17)) {
        *puVar1 = *puVar1 & 0xffffffef;
        _DAT_2001d158 = 1;
        _DAT_2001d154 = 0;
      }
LAB_08001b40:
      UNRECOVERED_JUMPTABLE = _DAT_2001d160;
    }
    if (UNRECOVERED_JUMPTABLE != (code *)0x0) {
      (*UNRECOVERED_JUMPTABLE)();
    }
  }
  puVar2 = _DAT_2001d120;
  if (_DAT_2001d178 == 0) {
    return;
  }
  UNRECOVERED_JUMPTABLE = _DAT_2001d170;
  if ((_DAT_2001d178 & 1) != 0) {
    uVar5 = uVar5 / 0x2580;
    *_DAT_2001d120 = *_DAT_2001d120 & 0xfffffffe;
    while ((((local_18 + 1 <= uVar5 && ((*puVar2 & 1) != 0)) && (local_18 + 2 <= uVar5)) &&
           (((*puVar2 & 1) != 0 && (local_18 + 3 <= uVar5))))) {
      if (((*puVar2 & 1) == 0) ||
         ((local_18 = local_18 + 4, uVar5 < local_18 || ((*puVar2 & 1) == 0)))) break;
    }
    _DAT_2001d158 = 1;
    _DAT_2001d154 = 0;
    UNRECOVERED_JUMPTABLE = _DAT_2001d170;
  }
joined_r0x08001b10:
  if (UNRECOVERED_JUMPTABLE == (code *)0x0) {
    return;
  }
                    /* WARNING: Could not recover jumptable at 0x08001bb6. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*UNRECOVERED_JUMPTABLE)();
  return;
}



/* 080013ec */

void DebugMon_Handler(void)

{
  return;
}



/* 080013f0 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void IRQ_40_Handler(void)

{
  if (-1 < _DAT_40013c14 << 0x13) {
    return;
  }
  _DAT_40013c14 = 0x1000;
  FUN_0800d7a8(_DAT_2001c208);
  return;
}



/* 08001414 */

void FUN_08001414(void)

{
  disableIRQinterrupts();
  do {
                    /* WARNING: Do nothing block with infinite loop */
  } while( true );
}



/* 0800141c */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined4 FUN_0800141c(int *param_1,uint *param_2)

{
  uint *puVar1;
  uint uVar2;
  int iVar3;
  int iVar4;
  uint uVar5;
  uint uVar6;
  int local_14;
  
  if (param_1[0xf] == 1) {
    return 2;
  }
  uVar6 = *param_2;
  param_1[0xf] = 1;
  uVar2 = uVar6 * 3;
  iVar4 = 0x10;
  if (9 < uVar6) {
    uVar2 = ((uVar6 & 0xffff) * 2 + (uVar6 & 0xffff)) - 0x1e;
    iVar4 = 0xc;
  }
  iVar3 = *param_1;
  *(uint *)(iVar3 + iVar4) = *(uint *)(iVar3 + iVar4) & ~(7 << (uVar2 & 0xff));
  *(uint *)(iVar3 + iVar4) = param_2[2] << (uVar2 & 0xff) | *(uint *)(iVar3 + iVar4);
  uVar2 = param_2[1];
  if (uVar2 < 7) {
    uVar2 = uVar2 * 5 - 5;
    puVar1 = (uint *)(iVar3 + 0x34);
    uVar5 = *puVar1;
  }
  else if (uVar2 < 0xd) {
    uVar2 = uVar2 * 5 - 0x23;
    puVar1 = (uint *)(iVar3 + 0x30);
    uVar5 = *puVar1;
  }
  else {
    uVar2 = uVar2 * 5 - 0x41;
    puVar1 = (uint *)(iVar3 + 0x2c);
    uVar5 = *puVar1;
  }
  *puVar1 = uVar5 & ~(0x1f << (uVar2 & 0xff));
  *puVar1 = (uVar6 & 0xffff) << (uVar2 & 0xff) | *puVar1;
  if (iVar3 == 0x40012000) {
    if (uVar6 == 0x12) {
      _DAT_40012304 = _DAT_40012304 | 0x400000;
    }
    else if ((((uVar6 & 0xfffffffe) == 0x10) &&
             (_DAT_40012304 = _DAT_40012304 | 0x800000, uVar6 == 0x10)) &&
            (local_14 = (_DAT_2001c064 / 1000000) * 10, local_14 != 0)) {
      while ((local_14 != 1 && (local_14 != 2))) {
        if ((local_14 == 3) || (local_14 = local_14 + -4, local_14 == 0)) break;
      }
    }
  }
  param_1[0xf] = 0;
  return 0;
}



/* 08001560 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined4 FUN_08001560(int *param_1)

{
  int iVar1;
  undefined4 uVar2;
  uint uVar3;
  int iVar4;
  int iVar5;
  
  if (param_1 != (int *)0x0) {
    if (param_1[0x10] == 0) {
      FUN_080016b8();
      param_1[0x11] = 0;
      param_1[0xf] = 0;
      iVar1 = param_1[0x10];
    }
    else {
      iVar1 = param_1[0x10];
    }
    if (iVar1 << 0x1b < 0) {
      uVar2 = 1;
    }
    else {
      param_1[0x10] = (param_1[0x10] & 0xffffeefdU) + 2;
      iVar1 = *param_1;
      uVar3 = param_1[2];
      _DAT_40012304 = _DAT_40012304 & 0xfffcffff | param_1[1];
      iVar4 = param_1[4];
      *(uint *)(iVar1 + 4) = *(uint *)(iVar1 + 4) & 0xfffffeff;
      *(uint *)(iVar1 + 4) = *(uint *)(iVar1 + 4) | iVar4 << 8;
      *(uint *)(iVar1 + 4) = *(uint *)(iVar1 + 4) & 0xfcffffff;
      *(uint *)(iVar1 + 4) = *(uint *)(iVar1 + 4) | uVar3;
      *(uint *)(iVar1 + 8) = *(uint *)(iVar1 + 8) & 0xfffff7ff;
      *(uint *)(iVar1 + 8) = param_1[3] | *(uint *)(iVar1 + 8);
      uVar3 = param_1[10];
      *(uint *)(iVar1 + 8) = *(uint *)(iVar1 + 8) & 0xf0ffffff;
      if (uVar3 == 0xf000001) {
        uVar3 = *(uint *)(iVar1 + 8) & 0xcfffffff;
      }
      else {
        *(uint *)(iVar1 + 8) = uVar3 | *(uint *)(iVar1 + 8);
        *(uint *)(iVar1 + 8) = *(uint *)(iVar1 + 8) & 0xcfffffff;
        uVar3 = param_1[0xb] | *(uint *)(iVar1 + 8);
      }
      *(uint *)(iVar1 + 8) = uVar3;
      *(uint *)(iVar1 + 8) = *(uint *)(iVar1 + 8) & 0xfffffffd;
      iVar4 = param_1[8];
      *(uint *)(iVar1 + 8) = *(uint *)(iVar1 + 8) | param_1[6] << 1;
      if (iVar4 == 0) {
        uVar3 = *(uint *)(iVar1 + 4) & 0xfffff7ff;
      }
      else {
        *(uint *)(iVar1 + 4) = *(uint *)(iVar1 + 4) | 0x800;
        *(uint *)(iVar1 + 4) = *(uint *)(iVar1 + 4) & 0xffff1fff;
        uVar3 = param_1[9] * 0x2000 - 0x2000U | *(uint *)(iVar1 + 4);
      }
      *(uint *)(iVar1 + 4) = uVar3;
      *(uint *)(iVar1 + 0x2c) = *(uint *)(iVar1 + 0x2c) & 0xff0fffff;
      iVar5 = param_1[5];
      iVar4 = param_1[0xc];
      *(uint *)(iVar1 + 0x2c) = *(uint *)(iVar1 + 0x2c) | param_1[7] * 0x100000 - 0x100000U;
      *(uint *)(iVar1 + 8) = *(uint *)(iVar1 + 8) & 0xfffffdff;
      *(uint *)(iVar1 + 8) = *(uint *)(iVar1 + 8) | iVar4 << 9;
      *(uint *)(iVar1 + 8) = *(uint *)(iVar1 + 8) & 0xfffffbff;
      *(uint *)(iVar1 + 8) = *(uint *)(iVar1 + 8) | iVar5 << 10;
      uVar2 = 0;
      param_1[0x11] = 0;
      param_1[0x10] = param_1[0x10] & 0xfffffffcU | 1;
    }
    param_1[0xf] = 0;
    return uVar2;
  }
  return 1;
}



/* 080016b8 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_080016b8(int *param_1,undefined4 param_2,undefined4 param_3,undefined4 param_4)

{
  int iVar1;
  undefined4 local_24;
  undefined4 local_20;
  undefined4 local_1c;
  undefined4 uStack_18;
  undefined4 local_14;
  
  local_14 = 0;
  uStack_18 = 0;
  if (*param_1 != 0x40012000) {
    return;
  }
  _DAT_40023844 = _DAT_40023844 | 0x100;
  _DAT_40023830 = _DAT_40023830 | 2;
  local_24 = 1;
  local_20 = 3;
  local_1c = 0;
  FUN_08001dd8(0x40020400,&local_24,_DAT_40023830,param_4,2);
  _DAT_2001cf90 = 0x40026410;
  _DAT_2001cf94 = 0;
  _DAT_2001cfa0 = 0x400;
  _DAT_2001cfa4 = 0x800;
  _DAT_2001cfa8 = 0x2000;
  _DAT_2001cfac = 0x100;
  _DAT_2001cf98 = 0;
  _DAT_2001cf9c = 0;
  _DAT_2001cfb0 = 0;
  _DAT_2001cfb4 = 0;
  iVar1 = FUN_08001bbc(&DAT_2001cf90);
  if (iVar1 != 0) {
    FUN_08001414();
  }
  param_1[0xe] = (int)&DAT_2001cf90;
  _DAT_2001cfcc = param_1;
  return;
}



/* 0800176c */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined4 FUN_0800176c(int *param_1,undefined4 param_2,undefined4 param_3)

{
  uint *puVar1;
  undefined4 *puVar2;
  uint uVar3;
  int iVar4;
  
  if (param_1[0xf] == 1) {
    return 2;
  }
  puVar2 = (undefined4 *)*param_1;
  param_1[0xf] = 1;
  if ((puVar2[2] & 1) == 0) {
    puVar2[2] = puVar2[2] | 1;
    for (iVar4 = (_DAT_2001c064 / 1000000) * 3;
        (((iVar4 != 0 && (iVar4 != 1)) && (iVar4 != 2)) && (iVar4 != 3)); iVar4 = iVar4 + -4) {
    }
  }
  if ((int)(puVar2[2] << 0x17) < 0) {
    puVar2[2] = puVar2[2] & 0xfffffeff;
  }
  if ((puVar2[2] & 1) == 0) {
    param_1[0x10] = param_1[0x10] | 0x10;
    puVar1 = (uint *)(param_1 + 0x11);
    uVar3 = 1;
  }
  else {
    param_1[0x10] = (param_1[0x10] & 0xfffff8feU) + 0x100;
    if ((int)(puVar2[1] << 0x15) < 0) {
      param_1[0x10] = param_1[0x10] & 0xffffcfffU | 0x1000;
    }
    uVar3 = 0;
    if (param_1[0x10] << 0x13 < 0) {
      uVar3 = param_1[0x11] & 0xfffffff9;
    }
    param_1[0x11] = uVar3;
    param_1[0xf] = 0;
    iVar4 = param_1[0xe];
    *(undefined1 **)(iVar4 + 0x40) = &LAB_08001314_1;
    *(undefined1 **)(iVar4 + 0x44) = &LAB_08001398_1;
    *(undefined1 **)(iVar4 + 0x50) = &LAB_08001384_1;
    *puVar2 = 0xffffffdd;
    puVar2[1] = puVar2[1] | 0x4000000;
    puVar2[2] = puVar2[2] | 0x100;
    FUN_08001d10(iVar4,puVar2 + 0x13,param_2,param_3);
    iVar4 = *param_1;
    if ((_DAT_40012304 & 0x1f) == 0) {
      if (iVar4 != 0x40012000) {
        if (iVar4 == 0x40012200) {
          if ((int)(_DAT_40012304 << 0x1b) < 0) {
            return 0;
          }
        }
        else {
          if (iVar4 != 0x40012100) {
            return 0;
          }
          if ((_DAT_40012304 & 0x1f) != 0) {
            return 0;
          }
        }
      }
      puVar1 = (uint *)(iVar4 + 8);
      if ((*puVar1 & 0x30000000) != 0) {
        return 0;
      }
      uVar3 = 0x40000000;
    }
    else {
      if (iVar4 != 0x40012000) {
        return 0;
      }
      if ((_DAT_40012008 & 0x30000000) != 0) {
        return 0;
      }
      puVar1 = (uint *)&DAT_40012008;
      uVar3 = 0x40000000;
    }
  }
  *puVar1 = uVar3 | *puVar1;
  return 0;
}



/* 08001908 */

undefined4 FUN_08001908(int param_1)

{
  if (param_1 == 0) {
    return 1;
  }
  if (*(int *)(param_1 + 8) == 0) {
    *(undefined4 *)(param_1 + 4) = 0;
    FUN_08001938();
    *(undefined4 *)(param_1 + 8) = 1;
    return 0;
  }
  *(undefined4 *)(param_1 + 8) = 1;
  return 0;
}



/* 08001938 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

int FUN_08001938(int *param_1)

{
  if (*param_1 != 0x40023000) {
    return *param_1;
  }
  _DAT_40023830 = _DAT_40023830 | 0x1000;
  return 0x1000;
}



/* 08001968 */

undefined4 FUN_08001968(int *param_1)

{
  int iVar1;
  uint *puVar2;
  int iVar3;
  int iVar4;
  
  iVar4 = param_1[0x17];
  iVar1 = FUN_08001f90();
  if (param_1[0xe] != 2) {
    param_1[0x16] = 0x80;
    param_1[0xd] = 0;
    return 1;
  }
  puVar2 = (uint *)*param_1;
  iVar3 = param_1[0x11];
  *puVar2 = *puVar2 & 0xffffffe9;
  puVar2[5] = puVar2[5] & 0xffffff7f;
  if ((iVar3 != 0) || (param_1[0x13] != 0)) {
    *puVar2 = *puVar2 & 0xfffffff7;
  }
  *puVar2 = *puVar2 & 0xfffffffe;
  do {
    if ((*(uint *)*param_1 & 1) == 0) {
      *(int *)(iVar4 + 8) = 0x3f << (param_1[0x18] & 0xffU);
      param_1[0xe] = 1;
      param_1[0xd] = 0;
      return 0;
    }
    iVar3 = FUN_08001f90();
  } while ((uint)(iVar3 - iVar1) < 6);
  param_1[0x16] = 0x20;
  param_1[0xe] = 3;
  param_1[0xd] = 0;
  return 3;
}



/* 080019e8 */

undefined4 FUN_080019e8(undefined4 *param_1)

{
  if (param_1[0xe] == 2) {
    param_1[0xe] = 5;
    *(uint *)*param_1 = *(uint *)*param_1 & 0xfffffffe;
    return 0;
  }
  param_1[0x16] = 0x80;
  return 1;
}



/* 08001a08 */

undefined4 FUN_08001a08(int param_1)

{
  return *(undefined4 *)(param_1 + 0x58);
}



/* 08001bbc */

undefined4 FUN_08001bbc(undefined4 *param_1)

{
  byte bVar1;
  int iVar2;
  int iVar3;
  undefined4 uVar4;
  uint *puVar5;
  uint uVar6;
  uint uVar7;
  undefined4 uVar8;
  uint uVar9;
  undefined4 uVar10;
  uint uVar11;
  uint uVar12;
  
  iVar2 = FUN_08001f90();
  if (param_1 == (undefined4 *)0x0) {
    return 1;
  }
  param_1[0xe] = 2;
  param_1[0xd] = 0;
  *(uint *)*param_1 = *(uint *)*param_1 & 0xfffffffe;
  do {
    puVar5 = (uint *)*param_1;
    if ((*puVar5 & 1) == 0) {
      uVar11 = param_1[6];
      uVar6 = param_1[9];
      uVar9 = param_1[3] | param_1[1] | *puVar5 & 0xf010803f | param_1[2] | param_1[4] | param_1[5]
              | param_1[7] | param_1[8] | uVar11;
      if (uVar6 != 4) {
        *puVar5 = uVar9;
        uVar6 = puVar5[5] & 0xfffffff8 | uVar6;
        goto switchD_08001cda_default;
      }
      uVar7 = param_1[10];
      uVar12 = param_1[0xb];
      *puVar5 = param_1[0xc] | uVar12 | uVar9;
      uVar6 = puVar5[5] & 0xfffffffc | uVar7 | 4;
      if (uVar12 == 0) goto switchD_08001cda_default;
      if (uVar11 == 0x2000) {
        uVar10 = 1;
        uVar8 = 0x40;
        uVar4 = 1;
        switch(uVar7) {
        case 0:
        case 2:
          goto LAB_08001bf4;
        case 1:
          goto switchD_08001cda_caseD_1;
        case 3:
switchD_08001cda_caseD_3:
          uVar9 = (uint)(uVar12 == 0x1800000);
          break;
        default:
          goto switchD_08001cda_default;
        }
      }
      else {
        if (uVar11 == 0) {
          if (uVar7 != 2) {
            if (uVar7 == 1) goto switchD_08001cda_caseD_3;
            if (uVar7 != 0) goto switchD_08001cda_default;
          }
        }
        else {
          if (uVar7 < 3) goto LAB_08001d02;
          if (uVar7 != 3) goto switchD_08001cda_default;
        }
switchD_08001cda_caseD_1:
        uVar9 = (uVar12 & 0x1ffffff) >> 0x18;
      }
      if (uVar9 != 0) {
LAB_08001d02:
        param_1[0x16] = 0x40;
        param_1[0xe] = 1;
        return 1;
      }
switchD_08001cda_default:
      uVar9 = ((uint)puVar5 & 0xf8) - 0x10;
      puVar5[5] = uVar6;
      bVar1 = (&DAT_080134c0)[uVar9 / 0x18];
      uVar6 = (uint)puVar5 & 0xfffffc00;
      if (0x5f < uVar9) {
        uVar6 = uVar6 + 4;
      }
      param_1[0x17] = uVar6;
      param_1[0x18] = (uint)bVar1;
      *(int *)(uVar6 + 8) = 0x3f << (uint)bVar1;
      param_1[0x16] = 0;
      param_1[0xe] = 1;
      return 0;
    }
    iVar3 = FUN_08001f90();
  } while ((uint)(iVar3 - iVar2) < 6);
  uVar10 = 3;
  uVar8 = 0x20;
  uVar4 = 3;
LAB_08001bf4:
  param_1[0x16] = uVar8;
  param_1[0xe] = uVar10;
  return uVar4;
}



/* 08001d10 */

undefined4 FUN_08001d10(undefined4 *param_1,uint param_2,uint param_3,uint param_4)

{
  uint uVar1;
  uint uVar2;
  int iVar3;
  int iVar4;
  uint *puVar5;
  int iVar6;
  
  if (param_1[0xd] == 1) {
    return 2;
  }
  param_1[0xd] = 1;
  iVar6 = param_1[0x17];
  if (param_1[0xe] != 1) {
    param_1[0xd] = 0;
    return 2;
  }
  param_1[0xe] = 2;
  param_1[0x16] = 0;
  puVar5 = (uint *)*param_1;
  iVar3 = param_1[2];
  iVar4 = param_1[0x11];
  uVar1 = param_1[0x18];
  *puVar5 = *puVar5 & 0xfffbffff;
  puVar5[1] = param_4;
  uVar2 = param_3;
  if (iVar3 == 0x40) {
    uVar2 = param_2;
    param_2 = param_3;
  }
  puVar5[2] = param_2;
  puVar5[3] = uVar2;
  *(int *)(iVar6 + 8) = 0x3f << (uVar1 & 0xff);
  *puVar5 = *puVar5 | 0x16;
  if (iVar4 != 0) {
    *puVar5 = *puVar5 | 8;
  }
  *puVar5 = *puVar5 | 1;
  return 0;
}



/* 08001db0 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_08001db0(uint param_1)

{
  int iVar1;
  int iVar2;
  
  iVar1 = FUN_08001f90();
  if (param_1 != 0xffffffff) {
    param_1 = param_1 + _DAT_2001c010;
  }
  do {
    iVar2 = FUN_08001f90();
  } while ((uint)(iVar2 - iVar1) < param_1);
  return;
}



/* 08001dd8 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_08001dd8(uint *param_1,uint *param_2)

{
  uint uVar1;
  uint uVar2;
  uint uVar3;
  uint uVar4;
  uint uVar5;
  uint uVar6;
  uint uVar7;
  uint uVar8;
  uint uVar9;
  uint uVar10;
  
  uVar1 = 8;
  if (param_1 == (uint *)0x40021c00) {
    uVar1 = 7;
  }
  uVar2 = 0;
  uVar5 = 0;
  uVar6 = 0;
  if (((uint)(param_1 + -0x10008000) >> 10 | (int)param_1 << 0x16) < 7) {
    uVar1 = (uint)(param_1 + -0x10008000) >> 10 | (int)param_1 << 0x16;
  }
  do {
    uVar10 = 1 << (uVar6 & 0xff);
    uVar7 = *param_2 & uVar10;
    uVar3 = _DAT_40013c00;
    if (uVar7 != 0) {
      uVar9 = param_2[1];
      uVar3 = uVar9 & 3;
      uVar8 = ~(3 << (uVar5 & 0xff));
      if (uVar3 - 1 < 2) {
        param_1[2] = param_1[2] & uVar8 | param_2[3] << (uVar5 & 0xff);
        param_1[1] = param_1[1] & ~uVar10 | ((uVar9 & 0x1f) >> 4) << (uVar6 & 0xff);
LAB_08001e80:
        param_1[3] = param_1[3] & uVar8 | param_2[2] << (uVar5 & 0xff);
        if (uVar3 == 2) {
          uVar3 = uVar6 >> 1 & 0xfffffffc;
          *(uint *)((int)param_1 + uVar3 + 0x20) =
               *(uint *)((int)param_1 + uVar3 + 0x20) & ~(0xf << (uVar2 & 0x1c)) |
               param_2[4] << (uVar2 & 0x1c);
          uVar9 = param_2[1];
          uVar3 = uVar9 & 3;
        }
      }
      else {
        if (uVar3 != 3) goto LAB_08001e80;
        uVar3 = 3;
      }
      *param_1 = *param_1 & uVar8 | uVar3 << (uVar5 & 0xff);
      uVar3 = _DAT_40013c00;
      if ((uVar9 & 0x30000) != 0) {
        _DAT_40023844 = _DAT_40023844 | 0x4000;
        *(uint *)((uVar6 & 0xfffffffc) + 0x40013808) =
             *(uint *)((uVar6 & 0xfffffffc) + 0x40013808) & ~(0xf << (uVar2 & 0xc)) |
             uVar1 << (uVar2 & 0xc);
        uVar10 = param_2[1];
        uVar8 = _DAT_40013c08 | uVar7;
        if (-1 < (int)(uVar10 << 0xb)) {
          uVar8 = _DAT_40013c08 & ~uVar7;
        }
        uVar9 = _DAT_40013c0c | uVar7;
        if (-1 < (int)(uVar10 << 10)) {
          uVar9 = _DAT_40013c0c & ~uVar7;
        }
        uVar4 = _DAT_40013c04 | uVar7;
        if (-1 < (int)(uVar10 << 0xe)) {
          uVar4 = _DAT_40013c04 & ~uVar7;
        }
        uVar3 = _DAT_40013c00 | uVar7;
        _DAT_40013c04 = uVar4;
        _DAT_40013c08 = uVar8;
        _DAT_40013c0c = uVar9;
        if (-1 < (int)(uVar10 << 0xf)) {
          uVar3 = _DAT_40013c00 & ~uVar7;
        }
      }
    }
    _DAT_40013c00 = uVar3;
    uVar6 = uVar6 + 1;
    uVar5 = uVar5 + 2;
    uVar2 = uVar2 + 4;
    if (uVar6 == 0x10) {
      return;
    }
  } while( true );
}



/* 08001f78 */

bool FUN_08001f78(int param_1,uint param_2)

{
  return (*(uint *)(param_1 + 0x10) & param_2) != 0;
}



/* 08001f84 */

void FUN_08001f84(int param_1,int param_2,int param_3)

{
  if (param_3 == 0) {
    param_2 = param_2 << 0x10;
  }
  *(int *)(param_1 + 0x18) = param_2;
  return;
}



/* 08001f90 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined4 FUN_08001f90(void)

{
  return _DAT_2001f1cc;
}



/* 08001f9c */

undefined4 FUN_08001f9c(int param_1)

{
  int iVar1;
  
  iVar1 = *(int *)(param_1 + 0x420);
  *(undefined1 *)(iVar1 + 0x42c) = 1;
  *(undefined1 *)(iVar1 + 0x42d) = 0;
  *(undefined1 *)(iVar1 + 0x42e) = 0;
  *(undefined4 *)(iVar1 + 0x4ec) = 1;
  FUN_0800d4f0(*(undefined4 *)(iVar1 + 0x4e4),iVar1 + 0x4ec,0,0);
  return 0;
}



/* 08001fa4 */

undefined4 FUN_08001fa4(int param_1)

{
  int iVar1;
  
  iVar1 = *(int *)(param_1 + 0x420);
  *(undefined1 *)(iVar1 + 0x42d) = 1;
  *(undefined1 *)(iVar1 + 0x42c) = 0;
  *(undefined1 *)(iVar1 + 0x42f) = 0;
  FUN_08008efc(iVar1);
  FUN_0800802c(iVar1,*(undefined1 *)(iVar1 + 0xc));
  FUN_0800802c(iVar1,*(undefined1 *)(iVar1 + 0xd));
  *(undefined4 *)(iVar1 + 0x4ec) = 1;
  FUN_0800d4f0(*(undefined4 *)(iVar1 + 0x4e4),iVar1 + 0x4ec,0,0);
  return 0;
}



/* 08001fac */

uint FUN_08001fac(int *param_1)

{
  return *(uint *)(*param_1 + 0x408) & 0xffff;
}



/* 08001fb4 */

void FUN_08001fb4(undefined4 *param_1)

{
  FUN_08009920(*param_1);
  return;
}



/* 08001fcc */

void FUN_08001fcc(undefined4 *param_1)

{
  if (param_1[0x105] != 1) {
    param_1[0x105] = 1;
    FUN_08009940(*param_1);
    param_1[0x105] = 0;
    return;
  }
  return;
}



/* 08001fd8 */

void FUN_08001fd8(undefined4 *param_1)

{
  param_1[0x105] = 1;
  FUN_08009940(*param_1);
  param_1[0x105] = 0;
  return;
}



/* 08001ff4 */

undefined4
FUN_08001ff4(undefined4 *param_1,int param_2,uint param_3,undefined4 param_4,int param_5,int param_6
            ,uint param_7)

{
  undefined4 uVar1;
  int iVar2;
  uint uVar3;
  
  if (param_1[0x105] != 1) {
    param_1[0x105] = 1;
    *(char *)(param_1 + param_2 * 0x10 + 5) = (char)param_4;
    *(byte *)((int)param_1 + param_2 * 0x40 + 0x16) = (byte)param_3 & 0x7f;
    *(char *)((int)param_1 + param_2 * 0x40 + 0x17) = (char)(param_3 >> 7);
    uVar1 = *param_1;
    *(undefined1 *)((int)param_1 + param_2 * 0x40 + 0x19) = 0;
    *(char *)((int)param_1 + param_2 * 0x40 + 0x15) = (char)param_2;
    *(char *)((int)param_1 + param_2 * 0x40 + 0x26) = (char)param_6;
    *(undefined2 *)((int)param_1 + param_2 * 0x40 + 0x1a) = 0;
    *(undefined2 *)(param_1 + param_2 * 0x10 + 9) = 0;
    iVar2 = FUN_08009920(uVar1);
    if (param_6 == 1) {
      uVar3 = param_7;
      if (0xbb < param_7) {
        uVar3 = 0xbc;
      }
      if (iVar2 != 0) {
        uVar3 = param_7;
      }
      if (param_5 == 1) {
        param_7 = uVar3;
      }
    }
    uVar1 = *param_1;
    *(char *)(param_1 + param_2 * 0x10 + 6) = (char)param_5;
    *(short *)(param_1 + param_2 * 0x10 + 10) = (short)param_7;
    uVar1 = FUN_08009ac4(uVar1,param_2,param_3,param_4,param_5,param_6,param_7);
    param_1[0x105] = 0;
    return uVar1;
  }
  return 2;
}



/* 08002098 */

undefined4 FUN_08002098(int param_1)

{
  int iVar1;
  
  iVar1 = *(int *)(param_1 + 0x420);
  *(undefined4 *)(iVar1 + 0x4ec) = 1;
  FUN_0800d4f0(*(undefined4 *)(iVar1 + 0x4e4),iVar1 + 0x4ec,0,0);
  return 0;
}



/* 080020a0 */

void FUN_080020a0(undefined4 *param_1,int param_2,int param_3,undefined4 param_4,int param_5,
                 undefined4 param_6,int param_7,undefined1 param_8)

{
  undefined4 uVar1;
  undefined1 uVar2;
  char cVar3;
  
  *(char *)((int)param_1 + param_2 * 0x40 + 0x17) = (char)param_3;
  *(char *)((int)param_1 + param_2 * 0x40 + 0x26) = (char)param_4;
  if (param_5 == 0) {
    *(undefined1 *)((int)param_1 + param_2 * 0x40 + 0x19) = param_8;
    uVar2 = 3;
  }
  else {
    uVar2 = 2;
  }
  *(undefined1 *)((int)param_1 + param_2 * 0x40 + 0x2a) = uVar2;
  cVar3 = '\0';
  switch(param_4) {
  case 0:
    if (param_5 != 1) goto switchD_080020d4_default;
    if (param_3 != 0) {
      if (*(char *)((int)param_1 + param_2 * 0x40 + 0x1a) != '\x01') goto switchD_080020d4_default;
      goto LAB_080020de;
    }
    if (param_7 == 0) {
      *(undefined1 *)((int)param_1 + param_2 * 0x40 + 0x3d) = 1;
      cVar3 = '\x02';
    }
    else if (*(char *)((int)param_1 + param_2 * 0x40 + 0x3d) != '\0') {
      cVar3 = '\x02';
    }
    break;
  case 1:
    break;
  case 2:
  case 3:
    if (param_3 == 0) {
      cVar3 = *(char *)((int)param_1 + param_2 * 0x40 + 0x3d);
    }
    else {
LAB_080020de:
      cVar3 = *(char *)(param_1 + param_2 * 0x10 + 0xf);
    }
    cVar3 = (cVar3 != '\0') << 1;
    break;
  default:
    goto switchD_080020d4_default;
  }
  *(char *)((int)param_1 + param_2 * 0x40 + 0x2a) = cVar3;
switchD_080020d4_default:
  uVar1 = *param_1;
  uVar2 = *(undefined1 *)((int)param_1 + 6);
  param_1[param_2 * 0x10 + 0xb] = param_6;
  param_1[param_2 * 0x10 + 0xd] = param_7;
  param_1[param_2 * 0x10 + 0xe] = 0;
  *(char *)((int)param_1 + param_2 * 0x40 + 0x15) = (char)param_2;
  param_1[param_2 * 0x10 + 0x13] = 0;
  param_1[param_2 * 0x10 + 0x14] = 0;
  FUN_08009bf4(uVar1,param_1 + param_2 * 0x10 + 5,uVar2);
  return;
}



/* 08002a9c */

bool FUN_08002a9c(int *param_1)

{
  int iVar1;
  int iVar2;
  
  if (param_1 == (int *)0x0) {
    return true;
  }
  iVar2 = *param_1;
  if (param_1[0x106] == 0) {
    param_1[0x105] = 0;
    FUN_08002b28(param_1);
  }
  param_1[0x106] = 3;
  if (iVar2 == 0x50000000) {
    *(undefined1 *)((int)param_1 + 6) = 0;
  }
  FUN_0800972c(*param_1);
  iVar2 = FUN_08009518(*param_1,param_1[1],param_1[2],param_1[3],(char)param_1[4]);
  if (iVar2 == 0) {
    iVar2 = FUN_0800a310(*param_1,1);
    if (iVar2 == 0) {
      iVar1 = FUN_08009eec(*param_1,param_1[1],param_1[2],param_1[3],(char)param_1[4]);
      iVar2 = 1;
      if (iVar1 != 0) {
        iVar2 = 2;
      }
      param_1[0x106] = iVar2;
      return iVar1 != 0;
    }
    param_1[0x106] = 2;
    return true;
  }
  param_1[0x106] = 2;
  return true;
}



/* 08002aa4 */

bool FUN_08002aa4(int *param_1)

{
  int iVar1;
  int iVar2;
  
  iVar2 = *param_1;
  if (param_1[0x106] == 0) {
    param_1[0x105] = 0;
    FUN_08002b28(param_1);
  }
  param_1[0x106] = 3;
  if (iVar2 == 0x50000000) {
    *(undefined1 *)((int)param_1 + 6) = 0;
  }
  FUN_0800972c(*param_1);
  iVar2 = FUN_08009518(*param_1,param_1[1],param_1[2],param_1[3],(char)param_1[4]);
  if (iVar2 == 0) {
    iVar2 = FUN_0800a310(*param_1,1);
    if (iVar2 == 0) {
      iVar1 = FUN_08009eec(*param_1,param_1[1],param_1[2],param_1[3],(char)param_1[4]);
      iVar2 = 1;
      if (iVar1 != 0) {
        iVar2 = 2;
      }
      param_1[0x106] = iVar2;
      return iVar1 != 0;
    }
    param_1[0x106] = 2;
    return true;
  }
  param_1[0x106] = 2;
  return true;
}



/* 08002b28 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

int FUN_08002b28(int *param_1,undefined4 param_2,undefined4 param_3,undefined4 param_4)

{
  undefined4 local_24;
  undefined4 local_20;
  undefined4 uStack_1c;
  undefined4 local_18;
  undefined4 local_14;
  
  if (*param_1 != 0x40040000) {
    return *param_1;
  }
  _DAT_40023830 = _DAT_40023830 | 2;
  local_24 = 0xc000;
  local_20 = 2;
  uStack_1c = 0;
  local_18 = 3;
  local_14 = 0xc;
  FUN_08001dd8(0x40020400,&local_24,param_3,param_4,2);
  _DAT_40023830 = _DAT_40023830 | 0x20000000;
  return 0x20000000;
}



/* 08002ba0 */

void FUN_08002ba0(int param_1)

{
  *(undefined1 *)(*(int *)(param_1 + 0x420) + 0x42f) = 0;
  return;
}



/* 08002ba8 */

void FUN_08002ba8(int param_1)

{
  int iVar1;
  
  iVar1 = *(int *)(param_1 + 0x420);
  *(undefined1 *)(iVar1 + 0x42f) = 1;
  *(undefined4 *)(iVar1 + 0x4ec) = 1;
  FUN_0800d4f0(*(undefined4 *)(iVar1 + 0x4e4),iVar1 + 0x4ec,0,0);
  return;
}



/* 08002bb0 */

undefined4 FUN_08002bb0(int *param_1)

{
  int iVar1;
  uint uVar2;
  
  iVar1 = *param_1;
  uVar2 = *(uint *)(iVar1 + 0x440);
  *(uint *)(iVar1 + 0x440) = uVar2 & 0xffffffd1 | 0x100;
  FUN_08001db0(100);
  *(uint *)(iVar1 + 0x440) = uVar2 & 0xfffffed1;
  FUN_08001db0(10);
  return 0;
}



/* 08002bb8 */

void FUN_08002bb8(int param_1)

{
  int *piVar1;
  
  piVar1 = *(int **)(param_1 + 0x420);
  piVar1[0x134] = piVar1[0x134] + 1;
  if (*piVar1 != 0xb) {
    return;
  }
  if (piVar1[0x122] != 0) {
                    /* WARNING: Could not recover jumptable at 0x08008daa. Too many branches */
                    /* WARNING: Treating indirect jump as call */
    (**(code **)(piVar1[0x122] + 0x18))();
    return;
  }
  return;
}



/* 08002bc0 */

void FUN_08002bc0(undefined4 *param_1)

{
  if (param_1[0x105] != 1) {
    param_1[0x105] = 1;
    FUN_0800973c(*param_1,1);
    FUN_08009788(*param_1);
    param_1[0x105] = 0;
    return;
  }
  return;
}



/* 08002bcc */

void FUN_08002bcc(undefined4 *param_1)

{
  param_1[0x105] = 1;
  FUN_0800973c(*param_1,1);
  FUN_08009788(*param_1);
  param_1[0x105] = 0;
  return;
}



/* 08002bf0 */

void FUN_08002bf0(undefined4 *param_1)

{
  if (param_1[0x105] != 1) {
    param_1[0x105] = 1;
    FUN_0800a678(*param_1);
    param_1[0x105] = 0;
    return;
  }
  return;
}



/* 08002c18 */

undefined4 FUN_08002c18(undefined4 *param_1)

{
  undefined4 *puVar1;
  int iVar2;
  int iVar3;
  undefined4 uVar4;
  undefined4 uVar5;
  uint uVar6;
  
  if (param_1 == (undefined4 *)0x0) {
    return 1;
  }
  puVar1 = (undefined4 *)*param_1;
  uVar4 = param_1[1];
  uVar5 = param_1[2];
  *puVar1 = 0xcccc;
  *puVar1 = 0x5555;
  puVar1[1] = uVar4;
  puVar1[2] = uVar5;
  iVar2 = FUN_08001f90();
  puVar1 = (undefined4 *)*param_1;
  uVar6 = puVar1[3];
  while( true ) {
    if ((uVar6 & 3) == 0) {
      *puVar1 = 0xaaaa;
      return 0;
    }
    iVar3 = FUN_08001f90();
    puVar1 = (undefined4 *)*param_1;
    if ((0x31 < (uint)(iVar3 - iVar2)) && ((puVar1[3] & 3) != 0)) break;
    uVar6 = puVar1[3];
  }
  return 3;
}



/* 08002c20 */

undefined4 FUN_08002c20(undefined4 *param_1)

{
  undefined4 *puVar1;
  int iVar2;
  int iVar3;
  undefined4 uVar4;
  undefined4 uVar5;
  uint uVar6;
  
  puVar1 = (undefined4 *)*param_1;
  uVar4 = param_1[1];
  uVar5 = param_1[2];
  *puVar1 = 0xcccc;
  *puVar1 = 0x5555;
  puVar1[1] = uVar4;
  puVar1[2] = uVar5;
  iVar2 = FUN_08001f90();
  puVar1 = (undefined4 *)*param_1;
  uVar6 = puVar1[3];
  while( true ) {
    if ((uVar6 & 3) == 0) {
      *puVar1 = 0xaaaa;
      return 0;
    }
    iVar3 = FUN_08001f90();
    puVar1 = (undefined4 *)*param_1;
    if ((0x31 < (uint)(iVar3 - iVar2)) && ((puVar1[3] & 3) != 0)) break;
    uVar6 = puVar1[3];
  }
  return 3;
}



/* 08002c74 */

undefined4 FUN_08002c74(undefined4 *param_1)

{
  *(undefined4 *)*param_1 = 0xaaaa;
  return 0;
}



/* 08002c9c */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined4 FUN_08002c9c(void)

{
  _DAT_40023c00 = _DAT_40023c00 | 0x700;
  FUN_08002e44(3);
  FUN_08002cd4(0xf);
  FUN_08002d88();
  return 0;
}



/* 08002cd4 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

int FUN_08002cd4(uint param_1)

{
  int iVar1;
  undefined1 auStack_28 [4];
  undefined4 local_24 [3];
  int local_18;
  
  _DAT_40023840 = _DAT_40023840 | 0x100;
  local_24[0] = 0x100;
  FUN_08002fd8(local_24,auStack_28);
  iVar1 = FUN_08003018();
  _DAT_2001db28 = (uint)(iVar1 << (local_18 != 0)) / 1000000 - 1;
  _DAT_2001db24 = 0x40002000;
  _DAT_2001db2c = 0;
  _DAT_2001db30 = 999;
  _DAT_2001db34 = 0;
  _DAT_2001db3c = 0;
  iVar1 = FUN_080037a0();
  if ((iVar1 == 0) && (iVar1 = FUN_080039d4(&DAT_2001db24), iVar1 == 0)) {
    FUN_08002dcc(0x2d);
    if (param_1 < 0x10) {
      FUN_08002dec(0x2d,param_1,0);
      _DAT_2001c00c = param_1;
      return 0;
    }
    return 1;
  }
  return iVar1;
}



/* 08002d88 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_08002d88(void)

{
  _DAT_40023844 = _DAT_40023844 | 0x4000;
  _DAT_40023840 = _DAT_40023840 | 0x10000000;
  FUN_08002dec(0xfffffffe,0xf,0);
  return;
}



/* 08002dcc */

void FUN_08002dcc(uint param_1)

{
  if ((int)param_1 < 0) {
    return;
  }
  *(int *)((param_1 >> 5) * 4 + -0x1fff1f00) = 1 << (param_1 & 0x1f);
  return;
}



/* 08002dec */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_08002dec(uint param_1,uint param_2,uint param_3)

{
  uint uVar1;
  undefined1 *puVar2;
  uint uVar3;
  uint uVar4;
  
  uVar4 = (_DAT_e000ed0c & 0x7ff) >> 8;
  uVar3 = uVar4 ^ 7;
  if (3 < uVar3) {
    uVar3 = 4;
  }
  uVar1 = uVar4 - 3;
  if (uVar4 < 3) {
    uVar1 = 0;
  }
  puVar2 = &DAT_e000e400 + param_1;
  if ((int)param_1 < 0) {
    puVar2 = (undefined1 *)((param_1 & 0xf) + 0xe000ed14);
  }
  *puVar2 = (char)(((param_2 & ~(-1 << uVar3)) << (uVar1 & 0xff) | param_3 & ~(-1 << (uVar1 & 0xff))
                   ) << 4);
  return;
}



/* 08002e44 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_08002e44(uint param_1)

{
  _DAT_e000ed0c = _DAT_e000ed0c & 0xf8ff | (param_1 & 7) << 8 | 0x5fa0000;
  return;
}



/* 08002e64 */

void FUN_08002e64(void)

{
  return;
}



/* 08002e68 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined4 FUN_08002e68(uint *param_1,uint param_2)

{
  uint uVar1;
  int iVar2;
  int iVar3;
  
  if (param_1 == (uint *)0x0) {
    return 1;
  }
  if ((_DAT_40023c00 & 7) < param_2) {
    _DAT_40023c00 = CONCAT31(DAT_40023c00_1,(char)param_2);
    if ((param_2 & 7) != param_2) {
      return 1;
    }
  }
  uVar1 = *param_1;
  if ((int)(uVar1 << 0x1e) < 0) {
    if ((int)(uVar1 << 0x1d) < 0) {
      _DAT_40023808 = _DAT_40023808 | 0x1c00;
    }
    if ((int)(uVar1 << 0x1c) < 0) {
      _DAT_40023808 = _DAT_40023808 | 0xe000;
    }
    _DAT_40023808 = _DAT_40023808 & 0xffffff0f | param_1[2];
  }
  if ((uVar1 & 1) != 0) {
    uVar1 = param_1[1];
    if (uVar1 - 2 < 2) {
      if (-1 < _DAT_40023800 << 6) {
        return 1;
      }
    }
    else if (uVar1 == 1) {
      if (-1 < _DAT_40023800 << 0xe) {
        return 1;
      }
    }
    else if (-1 < _DAT_40023800 << 0x1e) {
      return 1;
    }
    _DAT_40023808 = uVar1 | _DAT_40023808 & 0xfffffffc;
    iVar2 = FUN_08001f90();
    while ((_DAT_40023808 & 0xc) != param_1[1] * 4) {
      iVar3 = FUN_08001f90();
      if (5000 < (uint)(iVar3 - iVar2)) {
        return 3;
      }
    }
  }
  if (param_2 < (_DAT_40023c00 & 7)) {
    _DAT_40023c00 = CONCAT31(DAT_40023c00_1,(char)param_2);
    if ((param_2 & 7) != param_2) {
      return 1;
    }
  }
  if ((int)(*param_1 << 0x1d) < 0) {
    _DAT_40023808 = _DAT_40023808 & 0xffffe3ff | param_1[3];
  }
  if ((int)(*param_1 << 0x1c) < 0) {
    _DAT_40023808 = _DAT_40023808 & 0xffff1fff | param_1[4] << 3;
  }
  _DAT_2001c064 = FUN_08003068();
  _DAT_2001c064 = _DAT_2001c064 >> (&DAT_080132cf)[(_DAT_40023808 & 0xff) >> 4];
  FUN_08002cd4(_DAT_2001c00c);
  return 0;
}



/* 08002e70 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined4 FUN_08002e70(uint *param_1,uint param_2)

{
  uint uVar1;
  int iVar2;
  int iVar3;
  
  if ((_DAT_40023c00 & 7) < param_2) {
    _DAT_40023c00 = CONCAT31(DAT_40023c00_1,(char)param_2);
    if ((param_2 & 7) != param_2) {
      return 1;
    }
  }
  uVar1 = *param_1;
  if ((int)(uVar1 << 0x1e) < 0) {
    if ((int)(uVar1 << 0x1d) < 0) {
      _DAT_40023808 = _DAT_40023808 | 0x1c00;
    }
    if ((int)(uVar1 << 0x1c) < 0) {
      _DAT_40023808 = _DAT_40023808 | 0xe000;
    }
    _DAT_40023808 = _DAT_40023808 & 0xffffff0f | param_1[2];
  }
  if ((uVar1 & 1) != 0) {
    uVar1 = param_1[1];
    if (uVar1 - 2 < 2) {
      if (-1 < _DAT_40023800 << 6) {
        return 1;
      }
    }
    else if (uVar1 == 1) {
      if (-1 < _DAT_40023800 << 0xe) {
        return 1;
      }
    }
    else if (-1 < _DAT_40023800 << 0x1e) {
      return 1;
    }
    _DAT_40023808 = uVar1 | _DAT_40023808 & 0xfffffffc;
    iVar2 = FUN_08001f90();
    while ((_DAT_40023808 & 0xc) != param_1[1] * 4) {
      iVar3 = FUN_08001f90();
      if (5000 < (uint)(iVar3 - iVar2)) {
        return 3;
      }
    }
  }
  if (param_2 < (_DAT_40023c00 & 7)) {
    _DAT_40023c00 = CONCAT31(DAT_40023c00_1,(char)param_2);
    if ((param_2 & 7) != param_2) {
      return 1;
    }
  }
  if ((int)(*param_1 << 0x1d) < 0) {
    _DAT_40023808 = _DAT_40023808 & 0xffffe3ff | param_1[3];
  }
  if ((int)(*param_1 << 0x1c) < 0) {
    _DAT_40023808 = _DAT_40023808 & 0xffff1fff | param_1[4] << 3;
  }
  _DAT_2001c064 = FUN_08003068();
  _DAT_2001c064 = _DAT_2001c064 >> (&DAT_080132cf)[(_DAT_40023808 & 0xff) >> 4];
  FUN_08002cd4(_DAT_2001c00c);
  return 0;
}



/* 08002fcc */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_08002fcc(void)

{
  _DAT_4247004c = 1;
  return;
}



/* 08002fd8 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_08002fd8(undefined4 *param_1,uint *param_2)

{
  *param_1 = 0xf;
  param_1[1] = _DAT_40023808 & 3;
  param_1[2] = _DAT_40023808 & 0xf0;
  param_1[3] = _DAT_40023808 & 0x1c00;
  param_1[4] = _DAT_40023808 >> 3 & 0x1c00;
  *param_2 = _DAT_40023c00 & 7;
  return;
}



/* 08003018 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

uint FUN_08003018(void)

{
  return _DAT_2001c064 >> (&DAT_080132df)[(_DAT_40023808 & 0x1fff) >> 10];
}



/* 08003040 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

uint FUN_08003040(void)

{
  return _DAT_2001c064 >> (&DAT_080132df)[(_DAT_40023808 & 0xffff) >> 0xd];
}



/* 08003068 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

uint FUN_08003068(void)

{
  longlong lVar1;
  uint uVar2;
  
  if ((_DAT_40023808 & 0xc) != 8) {
    return 16000000;
  }
  lVar1 = (ulonglong)((_DAT_40023804 & 0x7fff) >> 6) * 16000000;
  uVar2 = FUN_08000326((int)lVar1,(int)((ulonglong)lVar1 >> 0x20),_DAT_40023804 & 0x3f,0);
  return uVar2 / (((_DAT_40023804 & 0x3ffff) >> 0x10) * 2 + 2);
}



/* 080030b0 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_080030b0(void)

{
  if (-1 < _DAT_4002380c << 0x18) {
    return;
  }
  FUN_08002e64();
  _DAT_4002380c = CONCAT12(0x80,_DAT_4002380c);
  return;
}



/* 080030cc */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined4 FUN_080030cc(byte *param_1)

{
  int iVar1;
  int iVar2;
  int iVar3;
  
  if (param_1 == (byte *)0x0) {
    return 1;
  }
  if ((*param_1 & 1) != 0) {
    if (((_DAT_40023808 & 0xc) == 4) ||
       (((_DAT_40023808 & 0xc) == 8 && ((int)(_DAT_40023804 << 9) < 0)))) {
      if (((int)(_DAT_40023800 << 0xe) < 0) && (*(int *)(param_1 + 4) == 0)) {
        return 1;
      }
    }
    else {
      iVar3 = *(int *)(param_1 + 4);
      if (iVar3 == 0x10000) {
LAB_08003224:
        _DAT_40023800 = _DAT_40023800 | 0x10000;
      }
      else {
        if (iVar3 == 0x50000) {
          _DAT_40023800 = _DAT_40023800 | 0x40000;
          goto LAB_08003224;
        }
        _DAT_40023800 = _DAT_40023800 & 0xfffaffff;
        if (iVar3 == 0) {
          iVar3 = FUN_08001f90();
          while ((int)(_DAT_40023800 << 0xe) < 0) {
            iVar2 = FUN_08001f90();
            if (100 < (uint)(iVar2 - iVar3)) {
              return 3;
            }
          }
          goto LAB_08003104;
        }
      }
      iVar3 = FUN_08001f90();
      while (-1 < (int)(_DAT_40023800 << 0xe)) {
        iVar2 = FUN_08001f90();
        if (100 < (uint)(iVar2 - iVar3)) {
          return 3;
        }
      }
    }
  }
LAB_08003104:
  if ((int)((uint)*param_1 << 0x1e) < 0) {
    if (((_DAT_40023808 & 0xc) == 0) ||
       (((_DAT_40023808 & 0xc) == 8 && (-1 < (int)(_DAT_40023804 << 9))))) {
      if (((int)(_DAT_40023800 << 0x1e) < 0) && (*(int *)(param_1 + 0xc) != 1)) {
        return 1;
      }
    }
    else {
      if (*(int *)(param_1 + 0xc) == 0) {
        uRam42470000 = 0;
        iVar3 = FUN_08001f90();
        while ((int)(_DAT_40023800 << 0x1e) < 0) {
          iVar2 = FUN_08001f90();
          if (2 < (uint)(iVar2 - iVar3)) {
            return 3;
          }
        }
        goto LAB_08003142;
      }
      uRam42470000 = 1;
      iVar3 = FUN_08001f90();
      while (-1 < (int)(_DAT_40023800 << 0x1e)) {
        iVar2 = FUN_08001f90();
        if (2 < (uint)(iVar2 - iVar3)) {
          return 3;
        }
      }
    }
    _DAT_40023800 = _DAT_40023800 & 0xffffff07 | *(int *)(param_1 + 0x10) << 3;
  }
LAB_08003142:
  if ((int)((uint)*param_1 << 0x1c) < 0) {
    if (*(int *)(param_1 + 0x14) == 0) {
      uRam42470e80 = 0;
      iVar3 = FUN_08001f90();
      while (_DAT_40023874 << 0x1e < 0) {
        iVar2 = FUN_08001f90();
        if (2 < (uint)(iVar2 - iVar3)) {
          return 3;
        }
      }
    }
    else {
      uRam42470e80 = 1;
      iVar3 = FUN_08001f90();
      while (-1 < _DAT_40023874 << 0x1e) {
        iVar2 = FUN_08001f90();
        if (2 < (uint)(iVar2 - iVar3)) {
          return 3;
        }
      }
    }
  }
  if (-1 < (int)((uint)*param_1 << 0x1d)) goto LAB_0800314e;
  iVar3 = _DAT_40023840 * 8;
  if (-1 < iVar3) {
    _DAT_40023840 = _DAT_40023840 | 0x10000000;
  }
  if (-1 < (int)(_DAT_40007000 << 0x17)) {
    _DAT_40007000 = _DAT_40007000 | 0x100;
    iVar2 = FUN_08001f90();
    while (-1 < (int)(_DAT_40007000 << 0x17)) {
      iVar1 = FUN_08001f90();
      if (2 < (uint)(iVar1 - iVar2)) {
        return 3;
      }
    }
  }
  iVar2 = *(int *)(param_1 + 8);
  if (iVar2 == 1) {
LAB_08003274:
    _DAT_40023870 = _DAT_40023870 | 1;
LAB_0800332a:
    iVar2 = FUN_08001f90();
    while (-1 < (int)(_DAT_40023870 << 0x1e)) {
      iVar1 = FUN_08001f90();
      if (5000 < (uint)(iVar1 - iVar2)) {
        return 3;
      }
    }
  }
  else {
    if (iVar2 == 5) {
      _DAT_40023870 = _DAT_40023870 | 4;
      goto LAB_08003274;
    }
    _DAT_40023870 = _DAT_40023870 & 0xfffffffa;
    if (iVar2 != 0) goto LAB_0800332a;
    iVar2 = FUN_08001f90();
    while ((int)(_DAT_40023870 << 0x1e) < 0) {
      iVar1 = FUN_08001f90();
      if (5000 < (uint)(iVar1 - iVar2)) {
        return 3;
      }
    }
  }
  if (-1 < iVar3) {
    _DAT_40023840 = _DAT_40023840 & 0xefffffff;
  }
LAB_0800314e:
  iVar3 = *(int *)(param_1 + 0x18);
  if (iVar3 != 0) {
    if ((_DAT_40023808 & 0xc) != 8) {
      uRam42470060 = 0;
      iVar2 = FUN_08001f90();
      if (iVar3 == 2) {
        do {
          if (-1 < (int)(_DAT_40023800 << 6)) {
            _DAT_40023804 =
                 *(uint *)(param_1 + 0x1c) | *(uint *)(param_1 + 0x20) |
                 *(int *)(param_1 + 0x24) << 6 | *(int *)(param_1 + 0x2c) << 0x18 |
                 (*(uint *)(param_1 + 0x28) & 0x1fffe) * 0x8000 - 0x10000;
            uRam42470060 = 1;
            iVar3 = FUN_08001f90();
            do {
              if ((int)(_DAT_40023800 << 6) < 0) {
                return 0;
              }
              iVar2 = FUN_08001f90();
            } while ((uint)(iVar2 - iVar3) < 3);
            return 3;
          }
          iVar3 = FUN_08001f90();
        } while ((uint)(iVar3 - iVar2) < 3);
      }
      else {
        do {
          if (-1 < (int)(_DAT_40023800 << 6)) {
            return 0;
          }
          iVar3 = FUN_08001f90();
        } while ((uint)(iVar3 - iVar2) < 3);
      }
      return 3;
    }
    if (iVar3 == 1) {
      return 1;
    }
    if (((((_DAT_40023804 & 0x400000) != *(uint *)(param_1 + 0x1c)) ||
         ((_DAT_40023804 & 0x3f) != *(uint *)(param_1 + 0x20))) ||
        ((_DAT_40023804 & 0x7fc0) != *(int *)(param_1 + 0x24) * 0x40)) ||
       (((_DAT_40023804 & 0x30000) != (*(uint *)(param_1 + 0x28) & 0x1fffe) * 0x8000 - 0x10000 ||
        ((_DAT_40023804 & 0xf000000) != *(int *)(param_1 + 0x2c) * 0x1000000)))) {
      return 1;
    }
  }
  return 0;
}



/* 080030d4 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined4 FUN_080030d4(byte *param_1)

{
  int iVar1;
  int iVar2;
  int iVar3;
  
  if ((*param_1 & 1) != 0) {
    if (((_DAT_40023808 & 0xc) == 4) ||
       (((_DAT_40023808 & 0xc) == 8 && ((int)(_DAT_40023804 << 9) < 0)))) {
      if (((int)(_DAT_40023800 << 0xe) < 0) && (*(int *)(param_1 + 4) == 0)) {
        return 1;
      }
    }
    else {
      iVar3 = *(int *)(param_1 + 4);
      if (iVar3 == 0x10000) {
LAB_08003224:
        _DAT_40023800 = _DAT_40023800 | 0x10000;
      }
      else {
        if (iVar3 == 0x50000) {
          _DAT_40023800 = _DAT_40023800 | 0x40000;
          goto LAB_08003224;
        }
        _DAT_40023800 = _DAT_40023800 & 0xfffaffff;
        if (iVar3 == 0) {
          iVar3 = FUN_08001f90();
          while ((int)(_DAT_40023800 << 0xe) < 0) {
            iVar2 = FUN_08001f90();
            if (100 < (uint)(iVar2 - iVar3)) {
              return 3;
            }
          }
          goto LAB_08003104;
        }
      }
      iVar3 = FUN_08001f90();
      while (-1 < (int)(_DAT_40023800 << 0xe)) {
        iVar2 = FUN_08001f90();
        if (100 < (uint)(iVar2 - iVar3)) {
          return 3;
        }
      }
    }
  }
LAB_08003104:
  if ((int)((uint)*param_1 << 0x1e) < 0) {
    if (((_DAT_40023808 & 0xc) == 0) ||
       (((_DAT_40023808 & 0xc) == 8 && (-1 < (int)(_DAT_40023804 << 9))))) {
      if (((int)(_DAT_40023800 << 0x1e) < 0) && (*(int *)(param_1 + 0xc) != 1)) {
        return 1;
      }
    }
    else {
      if (*(int *)(param_1 + 0xc) == 0) {
        uRam42470000 = 0;
        iVar3 = FUN_08001f90();
        while ((int)(_DAT_40023800 << 0x1e) < 0) {
          iVar2 = FUN_08001f90();
          if (2 < (uint)(iVar2 - iVar3)) {
            return 3;
          }
        }
        goto LAB_08003142;
      }
      uRam42470000 = 1;
      iVar3 = FUN_08001f90();
      while (-1 < (int)(_DAT_40023800 << 0x1e)) {
        iVar2 = FUN_08001f90();
        if (2 < (uint)(iVar2 - iVar3)) {
          return 3;
        }
      }
    }
    _DAT_40023800 = _DAT_40023800 & 0xffffff07 | *(int *)(param_1 + 0x10) << 3;
  }
LAB_08003142:
  if ((int)((uint)*param_1 << 0x1c) < 0) {
    if (*(int *)(param_1 + 0x14) == 0) {
      uRam42470e80 = 0;
      iVar3 = FUN_08001f90();
      while (_DAT_40023874 << 0x1e < 0) {
        iVar2 = FUN_08001f90();
        if (2 < (uint)(iVar2 - iVar3)) {
          return 3;
        }
      }
    }
    else {
      uRam42470e80 = 1;
      iVar3 = FUN_08001f90();
      while (-1 < _DAT_40023874 << 0x1e) {
        iVar2 = FUN_08001f90();
        if (2 < (uint)(iVar2 - iVar3)) {
          return 3;
        }
      }
    }
  }
  if (-1 < (int)((uint)*param_1 << 0x1d)) goto LAB_0800314e;
  iVar3 = _DAT_40023840 * 8;
  if (-1 < iVar3) {
    _DAT_40023840 = _DAT_40023840 | 0x10000000;
  }
  if (-1 < (int)(_DAT_40007000 << 0x17)) {
    _DAT_40007000 = _DAT_40007000 | 0x100;
    iVar2 = FUN_08001f90();
    while (-1 < (int)(_DAT_40007000 << 0x17)) {
      iVar1 = FUN_08001f90();
      if (2 < (uint)(iVar1 - iVar2)) {
        return 3;
      }
    }
  }
  iVar2 = *(int *)(param_1 + 8);
  if (iVar2 == 1) {
LAB_08003274:
    _DAT_40023870 = _DAT_40023870 | 1;
LAB_0800332a:
    iVar2 = FUN_08001f90();
    while (-1 < (int)(_DAT_40023870 << 0x1e)) {
      iVar1 = FUN_08001f90();
      if (5000 < (uint)(iVar1 - iVar2)) {
        return 3;
      }
    }
  }
  else {
    if (iVar2 == 5) {
      _DAT_40023870 = _DAT_40023870 | 4;
      goto LAB_08003274;
    }
    _DAT_40023870 = _DAT_40023870 & 0xfffffffa;
    if (iVar2 != 0) goto LAB_0800332a;
    iVar2 = FUN_08001f90();
    while ((int)(_DAT_40023870 << 0x1e) < 0) {
      iVar1 = FUN_08001f90();
      if (5000 < (uint)(iVar1 - iVar2)) {
        return 3;
      }
    }
  }
  if (-1 < iVar3) {
    _DAT_40023840 = _DAT_40023840 & 0xefffffff;
  }
LAB_0800314e:
  iVar3 = *(int *)(param_1 + 0x18);
  if (iVar3 != 0) {
    if ((_DAT_40023808 & 0xc) != 8) {
      uRam42470060 = 0;
      iVar2 = FUN_08001f90();
      if (iVar3 == 2) {
        do {
          if (-1 < (int)(_DAT_40023800 << 6)) {
            _DAT_40023804 =
                 *(uint *)(param_1 + 0x1c) | *(uint *)(param_1 + 0x20) |
                 *(int *)(param_1 + 0x24) << 6 | *(int *)(param_1 + 0x2c) << 0x18 |
                 (*(uint *)(param_1 + 0x28) & 0x1fffe) * 0x8000 - 0x10000;
            uRam42470060 = 1;
            iVar3 = FUN_08001f90();
            do {
              if ((int)(_DAT_40023800 << 6) < 0) {
                return 0;
              }
              iVar2 = FUN_08001f90();
            } while ((uint)(iVar2 - iVar3) < 3);
            return 3;
          }
          iVar3 = FUN_08001f90();
        } while ((uint)(iVar3 - iVar2) < 3);
      }
      else {
        do {
          if (-1 < (int)(_DAT_40023800 << 6)) {
            return 0;
          }
          iVar3 = FUN_08001f90();
        } while ((uint)(iVar3 - iVar2) < 3);
      }
      return 3;
    }
    if (iVar3 == 1) {
      return 1;
    }
    if (((((_DAT_40023804 & 0x400000) != *(uint *)(param_1 + 0x1c)) ||
         ((_DAT_40023804 & 0x3f) != *(uint *)(param_1 + 0x20))) ||
        ((_DAT_40023804 & 0x7fc0) != *(int *)(param_1 + 0x24) * 0x40)) ||
       (((_DAT_40023804 & 0x30000) != (*(uint *)(param_1 + 0x28) & 0x1fffe) * 0x8000 - 0x10000 ||
        ((_DAT_40023804 & 0xf000000) != *(int *)(param_1 + 0x2c) * 0x1000000)))) {
      return 1;
    }
  }
  return 0;
}



/* 08003480 */

undefined4 FUN_08003480(int *param_1)

{
  int iVar1;
  code *pcVar2;
  uint *puVar3;
  uint uVar4;
  uint uVar5;
  uint uVar6;
  uint uVar7;
  
  if (param_1 == (int *)0x0) {
    return 1;
  }
  if (param_1[9] == 0) {
    if (param_1[1] == 0x104) goto LAB_080034aa;
    iVar1 = 0x1c;
  }
  else {
    param_1[4] = 0;
    iVar1 = 0x14;
  }
  *(undefined4 *)((int)param_1 + iVar1) = 0;
LAB_080034aa:
  param_1[10] = 0;
  if (param_1[0x15] == 0) {
    param_1[0x17] = (int)&DAT_08003689;
    pcVar2 = (code *)param_1[0x1f];
    param_1[0x14] = 0;
    param_1[0x18] = (int)&DAT_08003681;
    param_1[0x19] = (int)&DAT_08003691;
    param_1[0x1a] = (int)&DAT_0800368d;
    param_1[0x1b] = (int)&DAT_08003685;
    param_1[0x1c] = (int)&DAT_08003695;
    param_1[0x1d] = (int)&DAT_0800347d;
    param_1[0x1e] = (int)&DAT_08003479;
    if (pcVar2 == (code *)0x0) {
      pcVar2 = (code *)0x8003595;
      param_1[0x1f] = 0x8003595;
    }
    (*pcVar2)();
  }
  param_1[0x15] = 2;
  puVar3 = (uint *)*param_1;
  uVar4 = param_1[1];
  uVar5 = param_1[2];
  uVar6 = param_1[3];
  *puVar3 = *puVar3 & 0xffffffbf;
  uVar7 = param_1[6];
  *puVar3 = (uVar4 & 0x104) + (uVar5 & 0x8400) + (uVar6 & 0x800) + (param_1[4] & 2U) +
            (param_1[5] & 1U) + (uVar7 & 0x200) + (param_1[7] & 0x38U) | param_1[8] & 0x80U |
            param_1[10] & 0x2000U;
  puVar3[1] = (uVar7 >> 0x10 & 4) + (param_1[9] & 0x10U);
  puVar3[7] = puVar3[7] & 0xfffff7ff;
  param_1[0x16] = 0;
  param_1[0x15] = 1;
  return 0;
}



/* 08003594 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_08003594(int *param_1)

{
  int iVar1;
  undefined4 local_38;
  undefined4 local_34;
  undefined4 local_30;
  undefined4 local_2c;
  undefined4 local_28;
  
  if (*param_1 != 0x40003800) {
    return;
  }
  _DAT_40023840 = _DAT_40023840 | 0x4000;
  _DAT_40023830 = _DAT_40023830 | 6;
  local_38 = 8;
  local_34 = 2;
  local_30 = 0;
  local_2c = 3;
  local_28 = 5;
  FUN_08001dd8(0x40020800,&local_38);
  local_38 = 0x2000;
  local_34 = 2;
  local_30 = 0;
  local_2c = 3;
  local_28 = 5;
  FUN_08001dd8(0x40020400,&local_38);
  _DAT_2001cff4 = 0x40026070;
  _DAT_2001cff8 = 0;
  _DAT_2001cffc = 0x40;
  _DAT_2001d000 = 0;
  _DAT_2001d004 = 0x400;
  _DAT_2001d008 = 0;
  _DAT_2001d00c = 0;
  _DAT_2001d010 = 0;
  _DAT_2001d014 = 0;
  _DAT_2001d018 = 0;
  iVar1 = FUN_08001bbc(&DAT_2001cff4);
  if (iVar1 != 0) {
    FUN_08001414();
  }
  param_1[0x12] = (int)&DAT_2001cff4;
  _DAT_2001d030 = param_1;
  return;
}



/* 080036a4 */

undefined4 FUN_080036a4(int *param_1,uint *param_2)

{
  if (param_1[0xf] != 1) {
    *(uint *)(*param_1 + 0x44) =
         param_2[7] |
         (param_2[2] & 0xffffc3ff | param_2[3] & 0xffffc0ff | param_2[1] & 0xffff87ff |
          *param_2 & 0xffff8fff | param_2[4] & 0xffff9fff | param_2[5]) & 0xffffbfff;
    param_1[0xf] = 0;
    return 0;
  }
  return 2;
}



/* 080036ec */

undefined4 FUN_080036ec(uint *param_1,uint *param_2)

{
  uint uVar1;
  uint uVar2;
  
  if (param_1[0xf] == 1) {
    return 2;
  }
  param_1[0x10] = 2;
  uVar1 = *param_1;
  *(uint *)(uVar1 + 4) = *(uint *)(uVar1 + 4) & 0xffffff8f | *param_2;
  if ((int)uVar1 < 0x40001800) {
    if ((int)uVar1 < 0x40000800) {
      if (uVar1 != 0x40000000) {
        uVar2 = 0x40000400;
LAB_08003780:
        if (uVar1 != uVar2) goto LAB_0800378e;
      }
    }
    else if (uVar1 != 0x40000800) {
      uVar2 = 0x40000c00;
      goto LAB_08003780;
    }
  }
  else if ((int)uVar1 < 0x40010400) {
    if (uVar1 != 0x40001800) {
      uVar2 = 0;
LAB_0800377c:
      uVar2 = uVar2 | 0x40010000;
      goto LAB_08003780;
    }
  }
  else if (uVar1 != 0x40014000) {
    uVar2 = 0x400;
    goto LAB_0800377c;
  }
  *(uint *)(uVar1 + 8) = param_2[1] | *(uint *)(uVar1 + 8) & 0xffffff7f;
LAB_0800378e:
  param_1[0x10] = 1;
  param_1[0xf] = 0;
  return 0;
}



/* 080037a0 */

undefined4 FUN_080037a0(undefined4 *param_1)

{
  code *pcVar1;
  
  if (param_1 != (undefined4 *)0x0) {
    if (param_1[0x10] == 0) {
      param_1[0xf] = 0;
      param_1[0x28] = &LAB_08004960_1;
      param_1[0x29] = &DAT_08004975;
      param_1[0x2a] = &DAT_08004979;
      param_1[0x2c] = &DAT_08003f7d;
      param_1[0x30] = &DAT_080047a5;
      param_1[0x31] = &DAT_08003f79;
      param_1[0x32] = &DAT_0800369d;
      pcVar1 = (code *)param_1[0x1a];
      param_1[0x2b] = &DAT_0800497d;
      param_1[0x2e] = &DAT_080043ad;
      param_1[0x2f] = &DAT_080047a1;
      param_1[0x2d] = &DAT_08003f81;
      param_1[0x33] = &DAT_080036a1;
      param_1[0x34] = &DAT_08003699;
      if (pcVar1 == (code *)0x0) {
        pcVar1 = (code *)0x8003885;
        param_1[0x1a] = 0x8003885;
      }
      (*pcVar1)(param_1);
    }
    param_1[0x10] = 2;
    FUN_0800725c(*param_1,param_1 + 1);
    param_1[0x19] = 1;
    param_1[0x11] = 1;
    param_1[0x12] = 1;
    param_1[0x13] = 1;
    param_1[0x14] = 1;
    param_1[0x15] = 1;
    param_1[0x16] = 1;
    param_1[0x17] = 1;
    param_1[0x18] = 1;
    param_1[0x10] = 1;
    return 0;
  }
  return 1;
}



/* 080037a8 */

undefined4 FUN_080037a8(undefined4 *param_1)

{
  code *pcVar1;
  
  if (param_1[0x10] == 0) {
    param_1[0xf] = 0;
    param_1[0x28] = &LAB_08004960_1;
    param_1[0x29] = &DAT_08004975;
    param_1[0x2a] = &DAT_08004979;
    param_1[0x2c] = &DAT_08003f7d;
    param_1[0x30] = &DAT_080047a5;
    param_1[0x31] = &DAT_08003f79;
    param_1[0x32] = &DAT_0800369d;
    pcVar1 = (code *)param_1[0x1a];
    param_1[0x2b] = &DAT_0800497d;
    param_1[0x2e] = &DAT_080043ad;
    param_1[0x2f] = &DAT_080047a1;
    param_1[0x2d] = &DAT_08003f81;
    param_1[0x33] = &DAT_080036a1;
    param_1[0x34] = &DAT_08003699;
    if (pcVar1 == (code *)0x0) {
      pcVar1 = (code *)0x8003885;
      param_1[0x1a] = 0x8003885;
    }
    (*pcVar1)(param_1);
  }
  param_1[0x10] = 2;
  FUN_0800725c(*param_1,param_1 + 1);
  param_1[0x19] = 1;
  param_1[0x11] = 1;
  param_1[0x12] = 1;
  param_1[0x13] = 1;
  param_1[0x14] = 1;
  param_1[0x15] = 1;
  param_1[0x16] = 1;
  param_1[0x17] = 1;
  param_1[0x18] = 1;
  param_1[0x10] = 1;
  return 0;
}



/* 08003884 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

int FUN_08003884(int *param_1)

{
  int iVar1;
  
  iVar1 = *param_1;
  if (iVar1 < 0x40010000) {
    if (iVar1 == 0x40001400) {
      _DAT_40023840 = _DAT_40023840 | 0x20;
      iVar1 = 0x20;
    }
    else if (iVar1 == 0x40001800) {
      _DAT_40023840 = _DAT_40023840 | 0x40;
      iVar1 = 0x40;
    }
    else if (iVar1 == 0x40001c00) {
      _DAT_40023840 = _DAT_40023840 | 0x80;
      iVar1 = 0x80;
    }
  }
  else if (iVar1 < 0x40014400) {
    if (iVar1 == 0x40010000) {
      _DAT_40023844 = _DAT_40023844 | 1;
      iVar1 = 1;
    }
    else if (iVar1 == 0x40014000) {
      _DAT_40023844 = _DAT_40023844 | 0x10000;
      iVar1 = 0x10000;
    }
  }
  else if (iVar1 == 0x40014400) {
    _DAT_40023844 = _DAT_40023844 | 0x20000;
    iVar1 = 0x20000;
  }
  else if (iVar1 == 0x40014800) {
    _DAT_40023844 = _DAT_40023844 | 0x40000;
    iVar1 = 0x40000;
  }
  return iVar1;
}



/* 080039d4 */

undefined4 FUN_080039d4(uint *param_1)

{
  uint *puVar1;
  uint uVar2;
  
  if (param_1[0x10] != 1) {
    return 1;
  }
  param_1[0x10] = 2;
  param_1 = (uint *)*param_1;
  param_1[3] = param_1[3] | 1;
  if ((int)param_1 < 0x40001800) {
    if ((int)param_1 < 0x40000800) {
      if (param_1 != (uint *)0x40000000) {
        puVar1 = (uint *)0x40000400;
LAB_08003a5c:
        if (param_1 != puVar1) goto LAB_08003a6e;
      }
    }
    else if (param_1 != (uint *)0x40000800) {
      puVar1 = (uint *)0x40000c00;
      goto LAB_08003a5c;
    }
  }
  else if ((int)param_1 < 0x40010400) {
    if (param_1 != (uint *)0x40001800) {
      uVar2 = 0;
LAB_08003a58:
      puVar1 = (uint *)(uVar2 | 0x40010000);
      goto LAB_08003a5c;
    }
  }
  else if (param_1 != (uint *)0x40014000) {
    uVar2 = 0x400;
    goto LAB_08003a58;
  }
  if ((param_1[2] & 7) == 6) {
    return 0;
  }
LAB_08003a6e:
  *param_1 = *param_1 | 1;
  return 0;
}



/* 08003a7c */

undefined4 FUN_08003a7c(int *param_1,uint *param_2)

{
  undefined4 uVar1;
  uint uVar2;
  uint uVar3;
  int iVar4;
  uint uVar5;
  
  if (param_1[0xf] == 1) {
    return 2;
  }
  param_1[0x10] = 2;
  iVar4 = *param_1;
  *(uint *)(iVar4 + 8) = *(uint *)(iVar4 + 8) & 0xffff0088;
  uVar2 = *param_2;
  if ((int)uVar2 < 0x50) {
    if ((int)uVar2 < 0x20) {
      if ((uVar2 == 0) || (uVar2 == 0x10)) goto LAB_08003b3a;
    }
    else {
      if ((uVar2 == 0x20) || (uVar2 == 0x30)) {
LAB_08003b3a:
        uVar2 = *(uint *)(iVar4 + 8) & 0xffffff8f | uVar2 | 7;
        goto LAB_08003b48;
      }
      if (uVar2 == 0x40) {
        uVar5 = param_2[1];
        uVar2 = param_2[3];
        uVar3 = *(uint *)(iVar4 + 0x20);
        *(uint *)(iVar4 + 0x20) = *(uint *)(iVar4 + 0x20) & 0xfffffffe;
        *(uint *)(iVar4 + 0x18) = *(uint *)(iVar4 + 0x18) & 0xffffff0f | uVar2 << 4;
        *(uint *)(iVar4 + 0x20) = uVar3 & 0xfffffff5 | uVar5;
        uVar2 = *(uint *)(iVar4 + 8) & 0xffffffcf | 0x47;
        goto LAB_08003b48;
      }
    }
LAB_08003c10:
    uVar1 = 1;
    goto LAB_08003b4e;
  }
  if ((int)uVar2 < 0x70) {
    if (uVar2 == 0x50) {
      uVar5 = param_2[1];
      uVar2 = param_2[3];
      uVar3 = *(uint *)(iVar4 + 0x20);
      *(uint *)(iVar4 + 0x20) = *(uint *)(iVar4 + 0x20) & 0xfffffffe;
      *(uint *)(iVar4 + 0x18) = *(uint *)(iVar4 + 0x18) & 0xffffff0f | uVar2 << 4;
      *(uint *)(iVar4 + 0x20) = uVar3 & 0xfffffff5 | uVar5;
      uVar2 = *(uint *)(iVar4 + 8) & 0xffffffdf | 0x57;
    }
    else {
      if (uVar2 != 0x60) goto LAB_08003c10;
      uVar5 = param_2[1];
      uVar2 = param_2[3];
      uVar3 = *(uint *)(iVar4 + 0x20);
      *(uint *)(iVar4 + 0x20) = *(uint *)(iVar4 + 0x20) & 0xffffffef;
      *(uint *)(iVar4 + 0x18) = *(uint *)(iVar4 + 0x18) & 0xffff0fff | uVar2 << 0xc;
      *(uint *)(iVar4 + 0x20) = uVar3 & 0xffffff5f | uVar5 << 4;
      uVar2 = *(uint *)(iVar4 + 8) & 0xffffffef | 0x67;
    }
LAB_08003b48:
    *(uint *)(iVar4 + 8) = uVar2;
  }
  else {
    if (uVar2 == 0x2000) {
      *(uint *)(iVar4 + 8) =
           param_2[2] | param_2[1] | param_2[3] << 8 | *(uint *)(iVar4 + 8) & 0xffff00ff;
      uVar2 = *(uint *)(iVar4 + 8) | 0x4000;
      goto LAB_08003b48;
    }
    if (uVar2 != 0x1000) {
      if (uVar2 != 0x70) goto LAB_08003c10;
      *(uint *)(iVar4 + 8) =
           param_2[2] | param_2[1] | param_2[3] << 8 | *(uint *)(iVar4 + 8) & 0xffff00ff;
      uVar2 = *(uint *)(iVar4 + 8) | 0x77;
      goto LAB_08003b48;
    }
  }
  uVar1 = 0;
LAB_08003b4e:
  param_1[0x10] = 1;
  param_1[0xf] = 0;
  return uVar1;
}



/* 08003c14 */

undefined4 FUN_08003c14(int *param_1,uint *param_2)

{
  int iVar1;
  code *pcVar2;
  uint uVar3;
  uint uVar4;
  uint uVar5;
  uint uVar6;
  uint uVar7;
  uint uVar8;
  uint uVar9;
  uint uVar10;
  
  if (param_1 != (int *)0x0) {
    if (param_1[0x10] == 0) {
      param_1[0xf] = 0;
      param_1[0x28] = (int)&LAB_08004960_1;
      param_1[0x29] = (int)&DAT_08004975;
      param_1[0x2a] = (int)&DAT_08004979;
      param_1[0x2b] = (int)&DAT_0800497d;
      param_1[0x2c] = (int)&DAT_08003f7d;
      param_1[0x2d] = (int)&DAT_08003f81;
      param_1[0x30] = (int)&DAT_080047a5;
      param_1[0x31] = (int)&DAT_08003f79;
      param_1[0x32] = (int)&DAT_0800369d;
      pcVar2 = (code *)param_1[0x24];
      param_1[0x2e] = (int)&DAT_080043ad;
      param_1[0x2f] = (int)&DAT_080047a1;
      param_1[0x33] = (int)&DAT_080036a1;
      param_1[0x34] = (int)&DAT_08003699;
      if (pcVar2 == (code *)0x0) {
        pcVar2 = (code *)0x8003d4d;
        param_1[0x24] = 0x8003d4d;
      }
      (*pcVar2)(param_1);
    }
    param_1[0x10] = 2;
    iVar1 = *param_1;
    *(uint *)(iVar1 + 8) = *(uint *)(iVar1 + 8) & 0xffffbff8;
    FUN_0800725c(iVar1,param_1 + 1);
    iVar1 = *param_1;
    uVar10 = param_2[1];
    uVar4 = param_2[2];
    uVar9 = param_2[3];
    uVar7 = param_2[6];
    uVar8 = param_2[7];
    uVar6 = param_2[8];
    uVar3 = param_2[4];
    uVar5 = param_2[5];
    *(uint *)(iVar1 + 8) = *param_2 | *(uint *)(iVar1 + 8);
    *(uint *)(iVar1 + 0x18) =
         *(uint *)(iVar1 + 0x18) & 0xffff0000 | uVar9 | (uVar4 | uVar7 << 8) & 0xffff0303 |
         uVar8 << 8 | uVar3 << 4 | uVar6 << 0xc;
    *(uint *)(iVar1 + 0x20) = *(uint *)(iVar1 + 0x20) & 0xffffff55 | uVar10 | uVar5 << 4;
    param_1[0x19] = 1;
    param_1[0x11] = 1;
    param_1[0x12] = 1;
    param_1[0x15] = 1;
    param_1[0x16] = 1;
    param_1[0x10] = 1;
    return 0;
  }
  return 1;
}



/* 08003c1c */

undefined4 FUN_08003c1c(int *param_1,uint *param_2)

{
  int iVar1;
  code *pcVar2;
  uint uVar3;
  uint uVar4;
  uint uVar5;
  uint uVar6;
  uint uVar7;
  uint uVar8;
  uint uVar9;
  uint uVar10;
  
  if (param_1[0x10] == 0) {
    param_1[0xf] = 0;
    param_1[0x28] = (int)&LAB_08004960_1;
    param_1[0x29] = (int)&DAT_08004975;
    param_1[0x2a] = (int)&DAT_08004979;
    param_1[0x2b] = (int)&DAT_0800497d;
    param_1[0x2c] = (int)&DAT_08003f7d;
    param_1[0x2d] = (int)&DAT_08003f81;
    param_1[0x30] = (int)&DAT_080047a5;
    param_1[0x31] = (int)&DAT_08003f79;
    param_1[0x32] = (int)&DAT_0800369d;
    pcVar2 = (code *)param_1[0x24];
    param_1[0x2e] = (int)&DAT_080043ad;
    param_1[0x2f] = (int)&DAT_080047a1;
    param_1[0x33] = (int)&DAT_080036a1;
    param_1[0x34] = (int)&DAT_08003699;
    if (pcVar2 == (code *)0x0) {
      pcVar2 = (code *)0x8003d4d;
      param_1[0x24] = 0x8003d4d;
    }
    (*pcVar2)(param_1);
  }
  param_1[0x10] = 2;
  iVar1 = *param_1;
  *(uint *)(iVar1 + 8) = *(uint *)(iVar1 + 8) & 0xffffbff8;
  FUN_0800725c(iVar1,param_1 + 1);
  iVar1 = *param_1;
  uVar10 = param_2[1];
  uVar4 = param_2[2];
  uVar9 = param_2[3];
  uVar7 = param_2[6];
  uVar8 = param_2[7];
  uVar6 = param_2[8];
  uVar3 = param_2[4];
  uVar5 = param_2[5];
  *(uint *)(iVar1 + 8) = *param_2 | *(uint *)(iVar1 + 8);
  *(uint *)(iVar1 + 0x18) =
       *(uint *)(iVar1 + 0x18) & 0xffff0000 | uVar9 | (uVar4 | uVar7 << 8) & 0xffff0303 | uVar8 << 8
       | uVar3 << 4 | uVar6 << 0xc;
  *(uint *)(iVar1 + 0x20) = *(uint *)(iVar1 + 0x20) & 0xffffff55 | uVar10 | uVar5 << 4;
  param_1[0x19] = 1;
  param_1[0x11] = 1;
  param_1[0x12] = 1;
  param_1[0x15] = 1;
  param_1[0x16] = 1;
  param_1[0x10] = 1;
  return 0;
}



/* 08003d4c */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_08003d4c(int *param_1)

{
  undefined4 uVar1;
  undefined4 *puVar2;
  undefined4 local_28;
  undefined4 local_24;
  undefined4 local_20;
  undefined4 local_1c;
  undefined4 local_18;
  
  switch(*param_1 + 0xc0000000U >> 10 | *param_1 << 0x16) {
  case 0:
    _DAT_40023840 = _DAT_40023840 | 1;
    uVar1 = 0x40020400;
    _DAT_40023830 = (undefined4 *)((uint)_DAT_40023830 | 3);
    local_28 = 0x8000;
    local_24 = 2;
    local_20 = 1;
    local_1c = 3;
    local_18 = 1;
    FUN_08001dd8(0x40020000,&local_28,1);
    local_28 = 8;
    local_20 = 1;
    local_1c = 3;
    puVar2 = &local_18;
    local_18 = 1;
    break;
  case 1:
    _DAT_40023840 = _DAT_40023840 | 2;
    local_28 = 0x30;
    local_1c = 3;
    goto LAB_08003eba;
  case 2:
    local_1c = 0;
    _DAT_40023840 = _DAT_40023840 | 4;
    local_28 = 0xc0;
LAB_08003eba:
    local_20 = 0;
    puVar2 = (undefined4 *)((uint)_DAT_40023830 | 2);
    local_18 = 2;
    uVar1 = 0x40020400;
    _DAT_40023830 = puVar2;
    break;
  case 3:
    _DAT_40023840 = _DAT_40023840 | 8;
    puVar2 = (undefined4 *)0x1;
    local_28 = 3;
    local_20 = 1;
    local_1c = 3;
    uVar1 = 0x40020000;
    local_18 = 2;
    _DAT_40023830 = (undefined4 *)((uint)_DAT_40023830 | 1);
    break;
  default:
    goto switchD_08003d6c_default;
  }
  local_24 = 2;
  FUN_08001dd8(uVar1,&local_28,puVar2);
switchD_08003d6c_default:
  return;
}



/* 08003ed0 */

undefined4 FUN_08003ed0(int *param_1,int param_2)

{
  uint *puVar1;
  uint uVar2;
  uint uVar3;
  
  if (param_2 == 4) {
    if (param_1[0x12] != 1 || param_1[0x16] != 1) {
      return 1;
    }
    param_1[0x12] = 2;
    param_1[0x16] = 2;
    puVar1 = (uint *)*param_1;
LAB_08003f46:
    uVar2 = 0x10;
    uVar3 = 0xffffffef;
  }
  else {
    if (param_2 == 0) {
      if (param_1[0x11] != 1 || param_1[0x15] != 1) {
        return 1;
      }
      param_1[0x11] = 2;
      param_1[0x15] = 2;
    }
    else {
      if (param_1[0x11] != 1 || param_1[0x12] != 1) {
        return 1;
      }
      if (param_1[0x15] != 1) {
        return 1;
      }
      if (param_1[0x16] != 1) {
        return 1;
      }
      param_1[0x11] = 2;
      param_1[0x12] = 2;
      param_1[0x15] = 2;
      param_1[0x16] = 2;
      if (param_2 != 0) {
        puVar1 = (uint *)*param_1;
        puVar1[8] = puVar1[8] & 0xfffffffe;
        puVar1[8] = puVar1[8] | 1;
        goto LAB_08003f46;
      }
    }
    puVar1 = (uint *)*param_1;
    uVar2 = 1;
    uVar3 = 0xfffffffe;
  }
  puVar1[8] = uVar3 & puVar1[8];
  puVar1[8] = uVar2 | puVar1[8];
  *puVar1 = *puVar1 | 1;
  return 0;
}



/* 080040dc */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_080040dc(int *param_1)

{
  int iVar1;
  undefined4 uVar2;
  undefined4 uVar3;
  undefined4 local_1c;
  undefined4 local_18;
  undefined4 local_14;
  undefined4 uStack_10;
  undefined4 local_c;
  
  iVar1 = *param_1;
  if (iVar1 < 0x40014400) {
    if (iVar1 == 0x40010000) {
      local_c = 1;
      _DAT_40023830 = _DAT_40023830 | 0x10;
      uStack_10 = 2;
      uVar2 = 0x10;
      uVar3 = 0x40021000;
      local_1c = 0x6a00;
    }
    else {
      if (iVar1 != 0x40014000) {
        return;
      }
      uStack_10 = 0;
      local_1c = 0x60;
      _DAT_40023830 = _DAT_40023830 | 0x10;
      local_c = 3;
      uVar2 = 0x10;
      uVar3 = 0x40021000;
    }
  }
  else {
    if (iVar1 == 0x40014400) {
      uStack_10 = 0;
      local_1c = 0x100;
    }
    else {
      if (iVar1 != 0x40014800) {
        return;
      }
      uStack_10 = 2;
      local_1c = 0x200;
    }
    uVar2 = 2;
    _DAT_40023830 = _DAT_40023830 | 2;
    local_c = 3;
    uVar3 = 0x40020400;
  }
  local_18 = 2;
  local_14 = 0;
  FUN_08001dd8(uVar3,&local_1c,local_c,0,uVar2);
  return;
}



/* 080041fc */

undefined4 FUN_080041fc(uint *param_1,uint *param_2,uint param_3)

{
  uint uVar1;
  uint uVar2;
  uint uVar3;
  uint uVar4;
  uint uVar5;
  
  if (param_1[0xf] != 1) {
    switch(param_3 >> 2 | param_3 << 0x1e) {
    case 0:
      uVar1 = *param_1;
      uVar2 = *(uint *)(uVar1 + 0x20);
      *(uint *)(uVar1 + 0x20) = *(uint *)(uVar1 + 0x20) & 0xfffffffe;
      uVar3 = *(uint *)(uVar1 + 4);
      uVar2 = uVar2 & 0xfffffffd | param_2[2];
      if ((uVar1 | 0x400) == 0x40010400) {
        uVar2 = uVar2 & 0xfffffff3 | param_2[3] & 0xfffffffb;
      }
      uVar4 = *param_2;
      if ((uVar1 | 0x400) == 0x40010400) {
        uVar3 = uVar3 & 0xfffffcff | param_2[5] | param_2[6];
      }
      *(uint *)(uVar1 + 4) = uVar3;
      *(uint *)(uVar1 + 0x18) = *(uint *)(uVar1 + 0x18) & 0xffffff8c | uVar4;
      *(uint *)(uVar1 + 0x34) = param_2[1];
      break;
    case 1:
      uVar1 = *param_1;
      uVar2 = *(uint *)(uVar1 + 0x20);
      *(uint *)(uVar1 + 0x20) = *(uint *)(uVar1 + 0x20) & 0xffffffef;
      uVar3 = *(uint *)(uVar1 + 4);
      uVar2 = uVar2 & 0xffffffdf | param_2[2] << 4;
      if ((uVar1 | 0x400) == 0x40010400) {
        uVar2 = uVar2 & 0xffffff3f | (param_2[3] & 0xffffffb) << 4;
      }
      uVar4 = *param_2;
      if ((uVar1 | 0x400) == 0x40010400) {
        uVar3 = uVar3 & 0xfffff3ff | (param_2[6] | param_2[5]) << 2;
      }
      *(uint *)(uVar1 + 4) = uVar3;
      *(uint *)(uVar1 + 0x18) = *(uint *)(uVar1 + 0x18) & 0xffff8cff | uVar4 << 8;
      *(uint *)(uVar1 + 0x38) = param_2[1];
      break;
    case 2:
      uVar1 = *param_1;
      uVar2 = *(uint *)(uVar1 + 0x20);
      *(uint *)(uVar1 + 0x20) = *(uint *)(uVar1 + 0x20) & 0xfffffeff;
      uVar3 = *(uint *)(uVar1 + 4);
      uVar2 = uVar2 & 0xfffffdff | param_2[2] << 8;
      if ((uVar1 | 0x400) == 0x40010400) {
        uVar2 = uVar2 & 0xfffff3ff | (param_2[3] & 0xfffffb) << 8;
      }
      uVar4 = *param_2;
      if ((uVar1 | 0x400) == 0x40010400) {
        uVar3 = uVar3 & 0xffffcfff | (param_2[6] | param_2[5]) << 4;
      }
      *(uint *)(uVar1 + 4) = uVar3;
      *(uint *)(uVar1 + 0x1c) = *(uint *)(uVar1 + 0x1c) & 0xffffff8c | uVar4;
      *(uint *)(uVar1 + 0x3c) = param_2[1];
      break;
    case 3:
      uVar1 = *param_1;
      uVar5 = *(uint *)(uVar1 + 0x20);
      *(uint *)(uVar1 + 0x20) = *(uint *)(uVar1 + 0x20) & 0xffffefff;
      uVar2 = *(uint *)(uVar1 + 4);
      uVar3 = *param_2;
      uVar4 = param_2[2];
      if ((uVar1 | 0x400) == 0x40010400) {
        uVar2 = uVar2 & 0xffffbfff | param_2[5] << 6;
      }
      *(uint *)(uVar1 + 4) = uVar2;
      *(uint *)(uVar1 + 0x1c) = *(uint *)(uVar1 + 0x1c) & 0xffff8cff | uVar3 << 8;
      uVar2 = uVar5 & 0xffffdfff | uVar4 << 0xc;
      *(uint *)(uVar1 + 0x40) = param_2[1];
      break;
    default:
      param_1[0xf] = 0;
      return 1;
    }
    *(uint *)(uVar1 + 0x20) = uVar2;
    param_1[0xf] = 0;
    return 0;
  }
  return 2;
}



/* 080043b0 */

undefined4 FUN_080043b0(undefined4 *param_1)

{
  code *pcVar1;
  
  if (param_1 != (undefined4 *)0x0) {
    if (param_1[0x10] == 0) {
      param_1[0xf] = 0;
      param_1[0x28] = &LAB_08004960_1;
      param_1[0x29] = &DAT_08004975;
      param_1[0x2a] = &DAT_08004979;
      param_1[0x2c] = &DAT_08003f7d;
      param_1[0x30] = &DAT_080047a5;
      param_1[0x31] = &DAT_08003f79;
      param_1[0x32] = &DAT_0800369d;
      pcVar1 = (code *)param_1[0x1e];
      param_1[0x2b] = &DAT_0800497d;
      param_1[0x2e] = &DAT_080043ad;
      param_1[0x2f] = &DAT_080047a1;
      param_1[0x2d] = &DAT_08003f81;
      param_1[0x33] = &DAT_080036a1;
      param_1[0x34] = &DAT_08003699;
      if (pcVar1 == (code *)0x0) {
        pcVar1 = (code *)0x8004495;
        param_1[0x1e] = 0x8004495;
      }
      (*pcVar1)(param_1);
    }
    param_1[0x10] = 2;
    FUN_0800725c(*param_1,param_1 + 1);
    param_1[0x19] = 1;
    param_1[0x11] = 1;
    param_1[0x12] = 1;
    param_1[0x13] = 1;
    param_1[0x14] = 1;
    param_1[0x15] = 1;
    param_1[0x16] = 1;
    param_1[0x17] = 1;
    param_1[0x18] = 1;
    param_1[0x10] = 1;
    return 0;
  }
  return 1;
}



/* 080043b8 */

undefined4 FUN_080043b8(undefined4 *param_1)

{
  code *pcVar1;
  
  if (param_1[0x10] == 0) {
    param_1[0xf] = 0;
    param_1[0x28] = &LAB_08004960_1;
    param_1[0x29] = &DAT_08004975;
    param_1[0x2a] = &DAT_08004979;
    param_1[0x2c] = &DAT_08003f7d;
    param_1[0x30] = &DAT_080047a5;
    param_1[0x31] = &DAT_08003f79;
    param_1[0x32] = &DAT_0800369d;
    pcVar1 = (code *)param_1[0x1e];
    param_1[0x2b] = &DAT_0800497d;
    param_1[0x2e] = &DAT_080043ad;
    param_1[0x2f] = &DAT_080047a1;
    param_1[0x2d] = &DAT_08003f81;
    param_1[0x33] = &DAT_080036a1;
    param_1[0x34] = &DAT_08003699;
    if (pcVar1 == (code *)0x0) {
      pcVar1 = (code *)0x8004495;
      param_1[0x1e] = 0x8004495;
    }
    (*pcVar1)(param_1);
  }
  param_1[0x10] = 2;
  FUN_0800725c(*param_1,param_1 + 1);
  param_1[0x19] = 1;
  param_1[0x11] = 1;
  param_1[0x12] = 1;
  param_1[0x13] = 1;
  param_1[0x14] = 1;
  param_1[0x15] = 1;
  param_1[0x16] = 1;
  param_1[0x17] = 1;
  param_1[0x18] = 1;
  param_1[0x10] = 1;
  return 0;
}



/* 08004494 */

void FUN_08004494(void)

{
  return;
}



/* 08004498 */

undefined4 FUN_08004498(uint *param_1,uint *param_2,uint param_3)

{
  uint *puVar1;
  uint uVar2;
  uint uVar3;
  uint uVar4;
  uint uVar5;
  uint uVar6;
  
  if (param_1[0xf] == 1) {
    return 2;
  }
  switch(param_3 >> 2 | param_3 << 0x1e) {
  case 0:
    uVar2 = *param_1;
    uVar3 = *(uint *)(uVar2 + 0x20);
    *(uint *)(uVar2 + 0x20) = *(uint *)(uVar2 + 0x20) & 0xfffffffe;
    uVar5 = *(uint *)(uVar2 + 4);
    puVar1 = (uint *)(uVar2 + 0x18);
    uVar4 = uVar3 & 0xfffffffd | param_2[2];
    if ((uVar2 | 0x400) == 0x40010400) {
      uVar4 = uVar4 & 0xfffffff3 | param_2[3] & 0xfffffffb;
    }
    uVar3 = *param_2;
    if ((uVar2 | 0x400) == 0x40010400) {
      uVar5 = uVar5 & 0xfffffcff | param_2[5] | param_2[6];
    }
    *(uint *)(uVar2 + 4) = uVar5;
    *(uint *)(uVar2 + 0x18) = uVar3 | *puVar1 & 0xffffff8c;
    uVar3 = param_2[4];
    *(uint *)(uVar2 + 0x34) = param_2[1];
    *(uint *)(uVar2 + 0x20) = uVar4;
    *(uint *)(uVar2 + 0x18) = *(uint *)(uVar2 + 0x18) | 8;
    *(uint *)(uVar2 + 0x18) = *(uint *)(uVar2 + 0x18) & 0xfffffffb;
    goto LAB_08004692;
  case 1:
    uVar2 = *param_1;
    uVar3 = *(uint *)(uVar2 + 0x20);
    *(uint *)(uVar2 + 0x20) = *(uint *)(uVar2 + 0x20) & 0xffffffef;
    uVar5 = *(uint *)(uVar2 + 4);
    puVar1 = (uint *)(uVar2 + 0x18);
    uVar4 = uVar3 & 0xffffffdf | param_2[2] << 4;
    if ((uVar2 | 0x400) == 0x40010400) {
      uVar4 = uVar4 & 0xffffff3f | (param_2[3] & 0xffffffb) << 4;
    }
    uVar3 = *param_2;
    if ((uVar2 | 0x400) == 0x40010400) {
      uVar5 = uVar5 & 0xfffff3ff | (param_2[6] | param_2[5]) << 2;
    }
    *(uint *)(uVar2 + 4) = uVar5;
    *(uint *)(uVar2 + 0x18) = *puVar1 & 0xffff8cff | uVar3 << 8;
    uVar3 = param_2[4];
    *(uint *)(uVar2 + 0x38) = param_2[1];
    *(uint *)(uVar2 + 0x20) = uVar4;
    *(uint *)(uVar2 + 0x18) = *(uint *)(uVar2 + 0x18) | 0x800;
    *(uint *)(uVar2 + 0x18) = *(uint *)(uVar2 + 0x18) & 0xfffffbff;
    break;
  case 2:
    uVar2 = *param_1;
    uVar3 = *(uint *)(uVar2 + 0x20);
    *(uint *)(uVar2 + 0x20) = *(uint *)(uVar2 + 0x20) & 0xfffffeff;
    uVar5 = *(uint *)(uVar2 + 4);
    puVar1 = (uint *)(uVar2 + 0x1c);
    uVar4 = uVar3 & 0xfffffdff | param_2[2] << 8;
    if ((uVar2 | 0x400) == 0x40010400) {
      uVar4 = uVar4 & 0xfffff3ff | (param_2[3] & 0xfffffb) << 8;
    }
    uVar3 = *param_2;
    if ((uVar2 | 0x400) == 0x40010400) {
      uVar5 = uVar5 & 0xffffcfff | (param_2[6] | param_2[5]) << 4;
    }
    *(uint *)(uVar2 + 4) = uVar5;
    *(uint *)(uVar2 + 0x1c) = *puVar1 & 0xffffff8c | uVar3;
    uVar3 = param_2[4];
    *(uint *)(uVar2 + 0x3c) = param_2[1];
    *(uint *)(uVar2 + 0x20) = uVar4;
    *(uint *)(uVar2 + 0x1c) = *(uint *)(uVar2 + 0x1c) | 8;
    *(uint *)(uVar2 + 0x1c) = *(uint *)(uVar2 + 0x1c) & 0xfffffffb;
    goto LAB_08004692;
  case 3:
    uVar2 = *param_1;
    uVar5 = *(uint *)(uVar2 + 0x20);
    *(uint *)(uVar2 + 0x20) = *(uint *)(uVar2 + 0x20) & 0xffffefff;
    uVar3 = *(uint *)(uVar2 + 4);
    puVar1 = (uint *)(uVar2 + 0x1c);
    uVar6 = *param_2;
    uVar4 = param_2[2];
    if ((uVar2 | 0x400) == 0x40010400) {
      uVar3 = uVar3 & 0xffffbfff | param_2[5] << 6;
    }
    *(uint *)(uVar2 + 4) = uVar3;
    *(uint *)(uVar2 + 0x1c) = *puVar1 & 0xffff8cff | uVar6 << 8;
    uVar3 = param_2[4];
    *(uint *)(uVar2 + 0x40) = param_2[1];
    *(uint *)(uVar2 + 0x20) = uVar5 & 0xffffdfff | uVar4 << 0xc;
    *(uint *)(uVar2 + 0x1c) = *(uint *)(uVar2 + 0x1c) | 0x800;
    *(uint *)(uVar2 + 0x1c) = *(uint *)(uVar2 + 0x1c) & 0xfffffbff;
    break;
  default:
    param_1[0xf] = 0;
    return 1;
  }
  uVar3 = uVar3 << 8;
LAB_08004692:
  *puVar1 = uVar3 | *puVar1;
  param_1[0xf] = 0;
  return 0;
}



/* 080046b4 */

undefined4 FUN_080046b4(undefined4 *param_1)

{
  code *pcVar1;
  
  if (param_1 != (undefined4 *)0x0) {
    if (param_1[0x10] == 0) {
      param_1[0xf] = 0;
      param_1[0x28] = &LAB_08004960_1;
      param_1[0x29] = &DAT_08004975;
      param_1[0x2a] = &DAT_08004979;
      param_1[0x2c] = &DAT_08003f7d;
      param_1[0x30] = &DAT_080047a5;
      param_1[0x31] = &DAT_08003f79;
      param_1[0x32] = &DAT_0800369d;
      pcVar1 = (code *)param_1[0x20];
      param_1[0x2b] = &DAT_0800497d;
      param_1[0x2e] = &DAT_080043ad;
      param_1[0x2f] = &DAT_080047a1;
      param_1[0x2d] = &DAT_08003f81;
      param_1[0x33] = &DAT_080036a1;
      param_1[0x34] = &DAT_08003699;
      if (pcVar1 == (code *)0x0) {
        pcVar1 = (code *)0x800479d;
        param_1[0x20] = 0x800479d;
      }
      (*pcVar1)(param_1);
    }
    param_1[0x10] = 2;
    FUN_0800725c(*param_1,param_1 + 1);
    param_1[0x19] = 1;
    param_1[0x11] = 1;
    param_1[0x12] = 1;
    param_1[0x13] = 1;
    param_1[0x14] = 1;
    param_1[0x15] = 1;
    param_1[0x16] = 1;
    param_1[0x17] = 1;
    param_1[0x18] = 1;
    param_1[0x10] = 1;
    return 0;
  }
  return 1;
}



/* 080046bc */

undefined4 FUN_080046bc(undefined4 *param_1)

{
  code *pcVar1;
  
  if (param_1[0x10] == 0) {
    param_1[0xf] = 0;
    param_1[0x28] = &LAB_08004960_1;
    param_1[0x29] = &DAT_08004975;
    param_1[0x2a] = &DAT_08004979;
    param_1[0x2c] = &DAT_08003f7d;
    param_1[0x30] = &DAT_080047a5;
    param_1[0x31] = &DAT_08003f79;
    param_1[0x32] = &DAT_0800369d;
    pcVar1 = (code *)param_1[0x20];
    param_1[0x2b] = &DAT_0800497d;
    param_1[0x2e] = &DAT_080043ad;
    param_1[0x2f] = &DAT_080047a1;
    param_1[0x2d] = &DAT_08003f81;
    param_1[0x33] = &DAT_080036a1;
    param_1[0x34] = &DAT_08003699;
    if (pcVar1 == (code *)0x0) {
      pcVar1 = (code *)0x800479d;
      param_1[0x20] = 0x800479d;
    }
    (*pcVar1)(param_1);
  }
  param_1[0x10] = 2;
  FUN_0800725c(*param_1,param_1 + 1);
  param_1[0x19] = 1;
  param_1[0x11] = 1;
  param_1[0x12] = 1;
  param_1[0x13] = 1;
  param_1[0x14] = 1;
  param_1[0x15] = 1;
  param_1[0x16] = 1;
  param_1[0x17] = 1;
  param_1[0x18] = 1;
  param_1[0x10] = 1;
  return 0;
}



/* 0800479c */

void FUN_0800479c(void)

{
  return;
}



/* 080048b8 */

undefined4 FUN_080048b8(uint *param_1,uint param_2)

{
  uint *puVar1;
  int iVar2;
  uint uVar3;
  
  puVar1 = (uint *)*param_1;
  puVar1[8] = puVar1[8] & ~(1 << (param_2 & 0x1f));
  puVar1[8] = puVar1[8];
  if (((((uint)puVar1 | 0x400) == 0x40010400) && ((puVar1[8] & 0x1111) == 0)) &&
     ((puVar1[8] & 0x444) == 0)) {
    puVar1[0x11] = puVar1[0x11] & 0xffff7fff;
    uVar3 = puVar1[8];
  }
  else {
    uVar3 = puVar1[8];
  }
  if (((uVar3 & 0x1111) == 0) && ((puVar1[8] & 0x444) == 0)) {
    *puVar1 = *puVar1 & 0xfffffffe;
  }
  if (param_2 != 0) {
    if (param_2 != 8) {
      if (param_2 == 4) {
        iVar2 = 0x48;
      }
      else {
        iVar2 = 0x50;
      }
      *(undefined4 *)((int)param_1 + iVar2) = 1;
      return 0;
    }
    param_1[0x13] = 1;
    return 0;
  }
  param_1[0x11] = 1;
  return 0;
}



/* 08004980 */

undefined4 FUN_08004980(int *param_1,int param_2,int param_3)

{
  bool bVar1;
  int iVar2;
  int iVar3;
  
  if (param_1[0x12] != 0x20) {
    return 2;
  }
  if (param_2 == 0 || param_3 == 0) {
    return 1;
  }
  param_1[0xc] = 1;
  param_1[0xd] = 0;
  param_1[10] = param_2;
  *(short *)(param_1 + 0xb) = (short)param_3;
  param_1[0x13] = 0;
  param_1[0x12] = 0x22;
  iVar3 = param_1[0xf];
  iVar2 = *param_1;
  *(undefined1 **)(iVar3 + 0x40) = &LAB_08007548_1;
  *(undefined1 **)(iVar3 + 0x44) = &LAB_080076a4_1;
  *(undefined1 **)(iVar3 + 0x50) = &LAB_080073d0_1;
  *(undefined4 *)(iVar3 + 0x54) = 0;
  FUN_08001d10(iVar3,iVar2 + 4,param_2,param_3);
  if (param_1[4] != 0) {
    do {
      ExclusiveAccess((uint *)(*param_1 + 0xc));
      bVar1 = (bool)hasExclusiveAccess((uint *)(*param_1 + 0xc));
      if (bVar1) {
        *(uint *)(*param_1 + 0xc) = *(uint *)(*param_1 + 0xc) | 0x100;
        goto LAB_08004a4c;
      }
      ExclusiveAccess((uint *)(*param_1 + 0xc));
      bVar1 = (bool)hasExclusiveAccess((uint *)(*param_1 + 0xc));
      if (bVar1) {
        *(uint *)(*param_1 + 0xc) = *(uint *)(*param_1 + 0xc) | 0x100;
        goto LAB_08004a4c;
      }
      ExclusiveAccess((uint *)(*param_1 + 0xc));
      bVar1 = (bool)hasExclusiveAccess((uint *)(*param_1 + 0xc));
      if (bVar1) {
        *(uint *)(*param_1 + 0xc) = *(uint *)(*param_1 + 0xc) | 0x100;
        goto LAB_08004a4c;
      }
      ExclusiveAccess((uint *)(*param_1 + 0xc));
      bVar1 = (bool)hasExclusiveAccess((uint *)(*param_1 + 0xc));
    } while (!bVar1);
    *(uint *)(*param_1 + 0xc) = *(uint *)(*param_1 + 0xc) | 0x100;
  }
LAB_08004a4c:
  do {
    ExclusiveAccess((uint *)(*param_1 + 0x14));
    bVar1 = (bool)hasExclusiveAccess((uint *)(*param_1 + 0x14));
    if (bVar1) {
      *(uint *)(*param_1 + 0x14) = *(uint *)(*param_1 + 0x14) | 1;
      goto LAB_08004ace;
    }
    ExclusiveAccess((uint *)(*param_1 + 0x14));
    bVar1 = (bool)hasExclusiveAccess((uint *)(*param_1 + 0x14));
    if (bVar1) {
      *(uint *)(*param_1 + 0x14) = *(uint *)(*param_1 + 0x14) | 1;
      goto LAB_08004ace;
    }
    ExclusiveAccess((uint *)(*param_1 + 0x14));
    bVar1 = (bool)hasExclusiveAccess((uint *)(*param_1 + 0x14));
    if (bVar1) {
      *(uint *)(*param_1 + 0x14) = *(uint *)(*param_1 + 0x14) | 1;
      goto LAB_08004ace;
    }
    ExclusiveAccess((uint *)(*param_1 + 0x14));
    bVar1 = (bool)hasExclusiveAccess((uint *)(*param_1 + 0x14));
  } while (!bVar1);
  *(uint *)(*param_1 + 0x14) = *(uint *)(*param_1 + 0x14) | 1;
LAB_08004ace:
  do {
    ExclusiveAccess((uint *)(*param_1 + 0x14));
    bVar1 = (bool)hasExclusiveAccess((uint *)(*param_1 + 0x14));
    if (bVar1) {
      *(uint *)(*param_1 + 0x14) = *(uint *)(*param_1 + 0x14) | 0x40;
      goto LAB_08004ae2;
    }
    ExclusiveAccess((uint *)(*param_1 + 0x14));
    bVar1 = (bool)hasExclusiveAccess((uint *)(*param_1 + 0x14));
    if (bVar1) {
      *(uint *)(*param_1 + 0x14) = *(uint *)(*param_1 + 0x14) | 0x40;
      goto LAB_08004ae2;
    }
    ExclusiveAccess((uint *)(*param_1 + 0x14));
    bVar1 = (bool)hasExclusiveAccess((uint *)(*param_1 + 0x14));
    if (bVar1) {
      *(uint *)(*param_1 + 0x14) = *(uint *)(*param_1 + 0x14) | 0x40;
      goto LAB_08004ae2;
    }
    ExclusiveAccess((uint *)(*param_1 + 0x14));
    bVar1 = (bool)hasExclusiveAccess((uint *)(*param_1 + 0x14));
  } while (!bVar1);
  *(uint *)(*param_1 + 0x14) = *(uint *)(*param_1 + 0x14) | 0x40;
LAB_08004ae2:
  if (param_1[0xc] != 1) {
    return 1;
  }
  do {
    ExclusiveAccess((uint *)(*param_1 + 0xc));
    bVar1 = (bool)hasExclusiveAccess((uint *)(*param_1 + 0xc));
    if (bVar1) {
      *(uint *)(*param_1 + 0xc) = *(uint *)(*param_1 + 0xc) | 0x10;
      return 0;
    }
    ExclusiveAccess((uint *)(*param_1 + 0xc));
    bVar1 = (bool)hasExclusiveAccess((uint *)(*param_1 + 0xc));
    if (bVar1) {
      *(uint *)(*param_1 + 0xc) = *(uint *)(*param_1 + 0xc) | 0x10;
      return 0;
    }
    ExclusiveAccess((uint *)(*param_1 + 0xc));
    bVar1 = (bool)hasExclusiveAccess((uint *)(*param_1 + 0xc));
    if (bVar1) {
      *(uint *)(*param_1 + 0xc) = *(uint *)(*param_1 + 0xc) | 0x10;
      return 0;
    }
    ExclusiveAccess((uint *)(*param_1 + 0xc));
    bVar1 = (bool)hasExclusiveAccess((uint *)(*param_1 + 0xc));
  } while (!bVar1);
  *(uint *)(*param_1 + 0xc) = *(uint *)(*param_1 + 0xc) | 0x10;
  return 0;
}



/* 080049a4 */

undefined4 FUN_080049a4(int *param_1,undefined4 param_2,int param_3)

{
  bool bVar1;
  int iVar2;
  int iVar3;
  undefined2 in_r12;
  
  param_1[0xc] = 1;
  param_1[0xd] = 0;
  param_1[10] = param_3;
  *(undefined2 *)(param_1 + 0xb) = in_r12;
  param_1[0x13] = 0;
  param_1[0x12] = 0x22;
  iVar3 = param_1[0xf];
  iVar2 = *param_1;
  *(undefined1 **)(iVar3 + 0x40) = &LAB_08007548_1;
  *(undefined1 **)(iVar3 + 0x44) = &LAB_080076a4_1;
  *(undefined1 **)(iVar3 + 0x50) = &LAB_080073d0_1;
  *(undefined4 *)(iVar3 + 0x54) = 0;
  FUN_08001d10(iVar3,iVar2 + 4);
  if (param_1[4] != 0) {
    do {
      ExclusiveAccess((uint *)(*param_1 + 0xc));
      bVar1 = (bool)hasExclusiveAccess((uint *)(*param_1 + 0xc));
      if (bVar1) {
        *(uint *)(*param_1 + 0xc) = *(uint *)(*param_1 + 0xc) | 0x100;
        goto LAB_08004a4c;
      }
      ExclusiveAccess((uint *)(*param_1 + 0xc));
      bVar1 = (bool)hasExclusiveAccess((uint *)(*param_1 + 0xc));
      if (bVar1) {
        *(uint *)(*param_1 + 0xc) = *(uint *)(*param_1 + 0xc) | 0x100;
        goto LAB_08004a4c;
      }
      ExclusiveAccess((uint *)(*param_1 + 0xc));
      bVar1 = (bool)hasExclusiveAccess((uint *)(*param_1 + 0xc));
      if (bVar1) {
        *(uint *)(*param_1 + 0xc) = *(uint *)(*param_1 + 0xc) | 0x100;
        goto LAB_08004a4c;
      }
      ExclusiveAccess((uint *)(*param_1 + 0xc));
      bVar1 = (bool)hasExclusiveAccess((uint *)(*param_1 + 0xc));
    } while (!bVar1);
    *(uint *)(*param_1 + 0xc) = *(uint *)(*param_1 + 0xc) | 0x100;
  }
LAB_08004a4c:
  do {
    ExclusiveAccess((uint *)(*param_1 + 0x14));
    bVar1 = (bool)hasExclusiveAccess((uint *)(*param_1 + 0x14));
    if (bVar1) {
      *(uint *)(*param_1 + 0x14) = *(uint *)(*param_1 + 0x14) | 1;
      goto LAB_08004ace;
    }
    ExclusiveAccess((uint *)(*param_1 + 0x14));
    bVar1 = (bool)hasExclusiveAccess((uint *)(*param_1 + 0x14));
    if (bVar1) {
      *(uint *)(*param_1 + 0x14) = *(uint *)(*param_1 + 0x14) | 1;
      goto LAB_08004ace;
    }
    ExclusiveAccess((uint *)(*param_1 + 0x14));
    bVar1 = (bool)hasExclusiveAccess((uint *)(*param_1 + 0x14));
    if (bVar1) {
      *(uint *)(*param_1 + 0x14) = *(uint *)(*param_1 + 0x14) | 1;
      goto LAB_08004ace;
    }
    ExclusiveAccess((uint *)(*param_1 + 0x14));
    bVar1 = (bool)hasExclusiveAccess((uint *)(*param_1 + 0x14));
  } while (!bVar1);
  *(uint *)(*param_1 + 0x14) = *(uint *)(*param_1 + 0x14) | 1;
LAB_08004ace:
  do {
    ExclusiveAccess((uint *)(*param_1 + 0x14));
    bVar1 = (bool)hasExclusiveAccess((uint *)(*param_1 + 0x14));
    if (bVar1) {
      *(uint *)(*param_1 + 0x14) = *(uint *)(*param_1 + 0x14) | 0x40;
      goto LAB_08004ae2;
    }
    ExclusiveAccess((uint *)(*param_1 + 0x14));
    bVar1 = (bool)hasExclusiveAccess((uint *)(*param_1 + 0x14));
    if (bVar1) {
      *(uint *)(*param_1 + 0x14) = *(uint *)(*param_1 + 0x14) | 0x40;
      goto LAB_08004ae2;
    }
    ExclusiveAccess((uint *)(*param_1 + 0x14));
    bVar1 = (bool)hasExclusiveAccess((uint *)(*param_1 + 0x14));
    if (bVar1) {
      *(uint *)(*param_1 + 0x14) = *(uint *)(*param_1 + 0x14) | 0x40;
      goto LAB_08004ae2;
    }
    ExclusiveAccess((uint *)(*param_1 + 0x14));
    bVar1 = (bool)hasExclusiveAccess((uint *)(*param_1 + 0x14));
  } while (!bVar1);
  *(uint *)(*param_1 + 0x14) = *(uint *)(*param_1 + 0x14) | 0x40;
LAB_08004ae2:
  if (param_1[0xc] != 1) {
    return 1;
  }
  do {
    ExclusiveAccess((uint *)(*param_1 + 0xc));
    bVar1 = (bool)hasExclusiveAccess((uint *)(*param_1 + 0xc));
    if (bVar1) {
      *(uint *)(*param_1 + 0xc) = *(uint *)(*param_1 + 0xc) | 0x10;
      return 0;
    }
    ExclusiveAccess((uint *)(*param_1 + 0xc));
    bVar1 = (bool)hasExclusiveAccess((uint *)(*param_1 + 0xc));
    if (bVar1) {
      *(uint *)(*param_1 + 0xc) = *(uint *)(*param_1 + 0xc) | 0x10;
      return 0;
    }
    ExclusiveAccess((uint *)(*param_1 + 0xc));
    bVar1 = (bool)hasExclusiveAccess((uint *)(*param_1 + 0xc));
    if (bVar1) {
      *(uint *)(*param_1 + 0xc) = *(uint *)(*param_1 + 0xc) | 0x10;
      return 0;
    }
    ExclusiveAccess((uint *)(*param_1 + 0xc));
    bVar1 = (bool)hasExclusiveAccess((uint *)(*param_1 + 0xc));
  } while (!bVar1);
  *(uint *)(*param_1 + 0xc) = *(uint *)(*param_1 + 0xc) | 0x10;
  return 0;
}



/* 08004b64 */

undefined4 FUN_08004b64(int *param_1)

{
  bool bVar1;
  int iVar2;
  
  do {
    ExclusiveAccess((uint *)(*param_1 + 0xc));
    bVar1 = (bool)hasExclusiveAccess((uint *)(*param_1 + 0xc));
    if (bVar1) {
      *(uint *)(*param_1 + 0xc) = *(uint *)(*param_1 + 0xc) & 0xfffffedf;
      goto LAB_08004bea;
    }
    ExclusiveAccess((uint *)(*param_1 + 0xc));
    bVar1 = (bool)hasExclusiveAccess((uint *)(*param_1 + 0xc));
    if (bVar1) {
      *(uint *)(*param_1 + 0xc) = *(uint *)(*param_1 + 0xc) & 0xfffffedf;
      goto LAB_08004bea;
    }
    ExclusiveAccess((uint *)(*param_1 + 0xc));
    bVar1 = (bool)hasExclusiveAccess((uint *)(*param_1 + 0xc));
    if (bVar1) {
      *(uint *)(*param_1 + 0xc) = *(uint *)(*param_1 + 0xc) & 0xfffffedf;
      goto LAB_08004bea;
    }
    ExclusiveAccess((uint *)(*param_1 + 0xc));
    bVar1 = (bool)hasExclusiveAccess((uint *)(*param_1 + 0xc));
  } while (!bVar1);
  *(uint *)(*param_1 + 0xc) = *(uint *)(*param_1 + 0xc) & 0xfffffedf;
LAB_08004bea:
  do {
    ExclusiveAccess((uint *)(*param_1 + 0x14));
    bVar1 = (bool)hasExclusiveAccess((uint *)(*param_1 + 0x14));
    if (bVar1) {
      *(uint *)(*param_1 + 0x14) = *(uint *)(*param_1 + 0x14) & 0xfffffffe;
      goto LAB_08004bfe;
    }
    ExclusiveAccess((uint *)(*param_1 + 0x14));
    bVar1 = (bool)hasExclusiveAccess((uint *)(*param_1 + 0x14));
    if (bVar1) {
      *(uint *)(*param_1 + 0x14) = *(uint *)(*param_1 + 0x14) & 0xfffffffe;
      goto LAB_08004bfe;
    }
    ExclusiveAccess((uint *)(*param_1 + 0x14));
    bVar1 = (bool)hasExclusiveAccess((uint *)(*param_1 + 0x14));
    if (bVar1) {
      *(uint *)(*param_1 + 0x14) = *(uint *)(*param_1 + 0x14) & 0xfffffffe;
      goto LAB_08004bfe;
    }
    ExclusiveAccess((uint *)(*param_1 + 0x14));
    bVar1 = (bool)hasExclusiveAccess((uint *)(*param_1 + 0x14));
  } while (!bVar1);
  *(uint *)(*param_1 + 0x14) = *(uint *)(*param_1 + 0x14) & 0xfffffffe;
LAB_08004bfe:
  if (param_1[0xc] == 1) {
    do {
      ExclusiveAccess((uint *)(*param_1 + 0xc));
      bVar1 = (bool)hasExclusiveAccess((uint *)(*param_1 + 0xc));
      if (bVar1) {
        *(uint *)(*param_1 + 0xc) = *(uint *)(*param_1 + 0xc) & 0xffffffef;
        goto LAB_08004c4e;
      }
      ExclusiveAccess((uint *)(*param_1 + 0xc));
      bVar1 = (bool)hasExclusiveAccess((uint *)(*param_1 + 0xc));
      if (bVar1) {
        *(uint *)(*param_1 + 0xc) = *(uint *)(*param_1 + 0xc) & 0xffffffef;
        goto LAB_08004c4e;
      }
      ExclusiveAccess((uint *)(*param_1 + 0xc));
      bVar1 = (bool)hasExclusiveAccess((uint *)(*param_1 + 0xc));
      if (bVar1) {
        *(uint *)(*param_1 + 0xc) = *(uint *)(*param_1 + 0xc) & 0xffffffef;
        goto LAB_08004c4e;
      }
      ExclusiveAccess((uint *)(*param_1 + 0xc));
      bVar1 = (bool)hasExclusiveAccess((uint *)(*param_1 + 0xc));
    } while (!bVar1);
    *(uint *)(*param_1 + 0xc) = *(uint *)(*param_1 + 0xc) & 0xffffffef;
  }
LAB_08004c4e:
  if (*(int *)(*param_1 + 0x14) << 0x19 < 0) {
    do {
      ExclusiveAccess((uint *)(*param_1 + 0x14));
      bVar1 = (bool)hasExclusiveAccess((uint *)(*param_1 + 0x14));
      if (bVar1) {
        *(uint *)(*param_1 + 0x14) = *(uint *)(*param_1 + 0x14) & 0xffffffbf;
        goto LAB_08004ca2;
      }
      ExclusiveAccess((uint *)(*param_1 + 0x14));
      bVar1 = (bool)hasExclusiveAccess((uint *)(*param_1 + 0x14));
      if (bVar1) {
        *(uint *)(*param_1 + 0x14) = *(uint *)(*param_1 + 0x14) & 0xffffffbf;
        goto LAB_08004ca2;
      }
      ExclusiveAccess((uint *)(*param_1 + 0x14));
      bVar1 = (bool)hasExclusiveAccess((uint *)(*param_1 + 0x14));
      if (bVar1) {
        *(uint *)(*param_1 + 0x14) = *(uint *)(*param_1 + 0x14) & 0xffffffbf;
        goto LAB_08004ca2;
      }
      ExclusiveAccess((uint *)(*param_1 + 0x14));
      bVar1 = (bool)hasExclusiveAccess((uint *)(*param_1 + 0x14));
    } while (!bVar1);
    *(uint *)(*param_1 + 0x14) = *(uint *)(*param_1 + 0x14) & 0xffffffbf;
LAB_08004ca2:
    if (param_1[0xf] != 0) {
      *(undefined4 *)(param_1[0xf] + 0x54) = 0;
      iVar2 = FUN_08001968();
      if ((iVar2 != 0) && (iVar2 = FUN_08001a08(param_1[0xf]), iVar2 == 0x20)) {
        param_1[0x13] = 0x10;
        return 3;
      }
    }
  }
  *(undefined2 *)((int)param_1 + 0x2e) = 0;
  param_1[0x12] = 0x20;
  param_1[0xc] = 0;
  return 0;
}



/* 08005244 */

void FUN_08005244(int *param_1)

{
  int iVar1;
  code *pcVar2;
  
  if (param_1 != (int *)0x0) {
    if (param_1[0x11] == 0) {
      param_1[0x10] = 0;
      param_1[0x15] = (int)&DAT_08005801;
      pcVar2 = (code *)param_1[0x1e];
      param_1[0x14] = (int)&DAT_08005805;
      param_1[0x16] = (int)&DAT_08005745;
      param_1[0x17] = (int)&DAT_08005741;
      param_1[0x18] = (int)&DAT_08004cd9;
      param_1[0x19] = (int)&DAT_08004b61;
      param_1[0x1a] = (int)&DAT_08004cd5;
      param_1[0x1b] = (int)&DAT_08004cd1;
      param_1[0x1d] = (int)&DAT_08004b5d;
      if (pcVar2 == (code *)0x0) {
        pcVar2 = (code *)0x8005305;
        param_1[0x1e] = 0x8005305;
      }
      (*pcVar2)(param_1);
    }
    param_1[0x11] = 0x24;
    *(uint *)(*param_1 + 0xc) = *(uint *)(*param_1 + 0xc) & 0xffffdfff;
    FUN_08007870(param_1);
    iVar1 = *param_1;
    *(uint *)(iVar1 + 0x10) = *(uint *)(iVar1 + 0x10) & 0xffffb7ff;
    *(uint *)(iVar1 + 0x14) = *(uint *)(iVar1 + 0x14) & 0xffffffd5;
    *(uint *)(iVar1 + 0xc) = *(uint *)(iVar1 + 0xc) | 0x2000;
    param_1[0x13] = 0;
    param_1[0x11] = 0x20;
    param_1[0x12] = 0x20;
    param_1[0xd] = 0;
    return;
  }
  return;
}



/* 0800524c */

void FUN_0800524c(int *param_1)

{
  int iVar1;
  code *pcVar2;
  
  if (param_1[0x11] == 0) {
    param_1[0x10] = 0;
    param_1[0x15] = (int)&DAT_08005801;
    pcVar2 = (code *)param_1[0x1e];
    param_1[0x14] = (int)&DAT_08005805;
    param_1[0x16] = (int)&DAT_08005745;
    param_1[0x17] = (int)&DAT_08005741;
    param_1[0x18] = (int)&DAT_08004cd9;
    param_1[0x19] = (int)&DAT_08004b61;
    param_1[0x1a] = (int)&DAT_08004cd5;
    param_1[0x1b] = (int)&DAT_08004cd1;
    param_1[0x1d] = (int)&DAT_08004b5d;
    if (pcVar2 == (code *)0x0) {
      pcVar2 = (code *)0x8005305;
      param_1[0x1e] = 0x8005305;
    }
    (*pcVar2)(param_1);
  }
  param_1[0x11] = 0x24;
  *(uint *)(*param_1 + 0xc) = *(uint *)(*param_1 + 0xc) & 0xffffdfff;
  FUN_08007870(param_1);
  iVar1 = *param_1;
  *(uint *)(iVar1 + 0x10) = *(uint *)(iVar1 + 0x10) & 0xffffb7ff;
  *(uint *)(iVar1 + 0x14) = *(uint *)(iVar1 + 0x14) & 0xffffffd5;
  *(uint *)(iVar1 + 0xc) = *(uint *)(iVar1 + 0xc) | 0x2000;
  param_1[0x13] = 0;
  param_1[0x11] = 0x20;
  param_1[0x12] = 0x20;
  param_1[0xd] = 0;
  return;
}



/* 08005304 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_08005304(int *param_1,undefined4 param_2,undefined4 param_3,undefined4 param_4)

{
  int iVar1;
  undefined4 uVar2;
  undefined4 uVar3;
  uint uVar4;
  undefined4 *puVar5;
  undefined4 local_34;
  undefined4 local_30;
  undefined4 local_2c;
  undefined4 local_28;
  undefined4 local_24;
  
  iVar1 = *param_1;
  if (iVar1 < 0x40005000) {
    if (iVar1 == 0x40004400) {
      _DAT_40023840 = _DAT_40023840 | 0x20000;
      _DAT_40023830 = _DAT_40023830 | 8;
      local_34 = 0x60;
      local_30 = 2;
      local_2c = 0;
      local_28 = 3;
      local_24 = 7;
      FUN_08001dd8(0x40020c00,&local_34,param_3,param_4,8);
      _DAT_2001d0bc = 0x40026088;
      _DAT_2001d0c0 = 0x8000000;
      uVar3 = 0x10000;
      _DAT_2001d0c4 = 0;
      _DAT_2001d0c8 = 0;
      _DAT_2001d0cc = 0x400;
      _DAT_2001d0d0 = 0;
      _DAT_2001d0d4 = 0;
      _DAT_2001d0d8 = 0;
      _DAT_2001d0dc = 0x10000;
      _DAT_2001d0e0 = 0;
      iVar1 = FUN_08001bbc(&DAT_2001d0bc);
      if (iVar1 != 0) {
        FUN_08001414();
      }
      param_1[0xf] = (int)&DAT_2001d0bc;
      uVar2 = 0x400260a0;
      puVar5 = (undefined4 *)&DAT_2001d120;
      _DAT_2001d0f8 = param_1;
    }
    else {
      if (iVar1 != 0x40004800) {
        return;
      }
      _DAT_40023840 = _DAT_40023840 | 0x40000;
      _DAT_40023830 = _DAT_40023830 | 8;
      local_34 = 0x300;
      local_30 = 2;
      local_2c = 0;
      local_28 = 3;
      local_24 = 7;
      FUN_08001dd8(0x40020c00,&local_34,param_3,param_4,8);
      _DAT_2001d184 = 0x40026028;
      _DAT_2001d188 = 0x8000000;
      uVar3 = 0x20000;
      _DAT_2001d18c = 0;
      _DAT_2001d190 = 0;
      _DAT_2001d194 = 0x400;
      _DAT_2001d198 = 0;
      _DAT_2001d19c = 0;
      _DAT_2001d1a0 = 0x100;
      _DAT_2001d1a4 = 0x20000;
      _DAT_2001d1a8 = 0;
      iVar1 = FUN_08001bbc(&DAT_2001d184);
      if (iVar1 != 0) {
        FUN_08001414();
      }
      param_1[0xf] = (int)&DAT_2001d184;
      uVar2 = 0x40026058;
      puVar5 = (undefined4 *)&DAT_2001d1e8;
      _DAT_2001d1c0 = param_1;
    }
    *puVar5 = uVar2;
    puVar5[1] = 0x8000000;
    puVar5[2] = 0x40;
    puVar5[3] = 0;
    puVar5[4] = 0x400;
    puVar5[5] = 0;
    puVar5[6] = 0;
    puVar5[7] = 0;
    puVar5[8] = uVar3;
    puVar5[9] = 0;
    iVar1 = FUN_08001bbc(puVar5);
    if (iVar1 != 0) {
      FUN_08001414();
    }
    param_1[0xe] = (int)puVar5;
    puVar5[0xf] = param_1;
    return;
  }
  if (iVar1 == 0x40011400) {
    _DAT_40023844 = _DAT_40023844 | 0x20;
    uVar4 = 0x20;
    _DAT_40023830 = _DAT_40023830 | 4;
    uVar3 = 4;
    local_34 = 0xc0;
    local_2c = 1;
    local_24 = 8;
    iVar1 = -0x400;
  }
  else {
    if (iVar1 != 0x40011000) {
      if (iVar1 != 0x40005000) {
        return;
      }
      _DAT_40023840 = _DAT_40023840 | 0x100000;
      _DAT_40023830 = _DAT_40023830 | 0xc;
      local_34 = 0x1000;
      local_30 = 2;
      local_2c = 0;
      local_28 = 3;
      local_24 = 8;
      FUN_08001dd8(0x40020800,&local_34,param_3,param_4,_DAT_40023830 & 8);
      local_34 = 4;
      local_30 = 2;
      local_2c = 0;
      local_28 = 3;
      local_24 = 8;
      FUN_08001dd8(0x40020c00,&local_34);
      _DAT_2001d058 = 0x40026010;
      _DAT_2001d05c = 0x8000000;
      _DAT_2001d060 = 0;
      _DAT_2001d078 = 0x10000;
      _DAT_2001d07c = 0;
      _DAT_2001d064 = 0;
      _DAT_2001d068 = 0x400;
      _DAT_2001d06c = 0;
      _DAT_2001d070 = 0;
      _DAT_2001d074 = 0;
      iVar1 = FUN_08001bbc(&DAT_2001d058);
      if (iVar1 != 0) {
        FUN_08001414();
      }
      param_1[0xf] = (int)&DAT_2001d058;
      _DAT_2001d094 = param_1;
      return;
    }
    _DAT_40023844 = _DAT_40023844 | 0x10;
    uVar4 = _DAT_40023830 | 1;
    uVar3 = 1;
    local_34 = 0x600;
    local_2c = 0;
    local_24 = 7;
    iVar1 = -0xc00;
    _DAT_40023830 = uVar4;
  }
  local_28 = 3;
  local_30 = 2;
  FUN_08001dd8(iVar1 + 0x40020c00,&local_34,uVar4,param_4,uVar3);
  return;
}



/* 08005678 */

undefined4 FUN_08005678(int param_1,int param_2,int param_3)

{
  if (param_3 != 0) {
    if (*(int *)(param_1 + 0x44) == 0x20) {
      switch(param_2) {
      case 0:
        *(int *)(param_1 + 0x50) = param_3;
        return 0;
      case 1:
        *(int *)(param_1 + 0x54) = param_3;
        return 0;
      case 2:
        *(int *)(param_1 + 0x58) = param_3;
        return 0;
      case 3:
        *(int *)(param_1 + 0x5c) = param_3;
        return 0;
      case 4:
        *(int *)(param_1 + 0x60) = param_3;
        return 0;
      case 5:
        *(int *)(param_1 + 100) = param_3;
        return 0;
      case 6:
        *(int *)(param_1 + 0x68) = param_3;
        return 0;
      case 7:
        *(int *)(param_1 + 0x6c) = param_3;
        return 0;
      case 0xb:
switchD_08005684_caseD_b:
        *(int *)(param_1 + 0x78) = param_3;
        return 0;
      case 0xc:
switchD_08005684_caseD_c:
        *(int *)(param_1 + 0x7c) = param_3;
        return 0;
      }
    }
    else if (*(int *)(param_1 + 0x44) == 0) {
      if (param_2 == 0xc) goto switchD_08005684_caseD_c;
      if (param_2 == 0xb) goto switchD_08005684_caseD_b;
    }
  }
  *(uint *)(param_1 + 0x4c) = *(uint *)(param_1 + 0x4c) | 0x20;
  return 1;
}



/* 08005700 */

undefined4 FUN_08005700(int param_1,int param_2)

{
  if (param_2 == 0) {
    *(uint *)(param_1 + 0x4c) = *(uint *)(param_1 + 0x4c) | 0x20;
    return 1;
  }
  if (*(int *)(param_1 + 0x40) != 1) {
    if (*(int *)(param_1 + 0x44) != 0x20) {
      *(uint *)(param_1 + 0x4c) = *(uint *)(param_1 + 0x4c) | 0x20;
      *(undefined4 *)(param_1 + 0x40) = 0;
      return 1;
    }
    *(int *)(param_1 + 0x74) = param_2;
    *(undefined4 *)(param_1 + 0x40) = 0;
    return 0;
  }
  return 2;
}



/* 08005748 */

undefined4 FUN_08005748(int *param_1,int param_2,int param_3)

{
  bool bVar1;
  int iVar2;
  int iVar3;
  
  if (param_1[0x11] != 0x20) {
    return 2;
  }
  if (param_2 == 0 || param_3 == 0) {
    return 1;
  }
  param_1[8] = param_2;
  *(short *)(param_1 + 9) = (short)param_3;
  *(short *)((int)param_1 + 0x26) = (short)param_3;
  param_1[0x13] = 0;
  param_1[0x11] = 0x21;
  iVar3 = param_1[0xe];
  iVar2 = *param_1;
  *(undefined1 **)(iVar3 + 0x40) = &LAB_080076bc_1;
  *(undefined1 **)(iVar3 + 0x44) = &LAB_0800776c_1;
  *(undefined1 **)(iVar3 + 0x50) = &LAB_080073d0_1;
  *(undefined4 *)(iVar3 + 0x54) = 0;
  FUN_08001d10(iVar3,param_2,iVar2 + 4);
  *(undefined4 *)*param_1 = 0xffffffbf;
  do {
    ExclusiveAccess((uint *)(*param_1 + 0x14));
    bVar1 = (bool)hasExclusiveAccess((uint *)(*param_1 + 0x14));
    if (bVar1) {
      *(uint *)(*param_1 + 0x14) = *(uint *)(*param_1 + 0x14) | 0x80;
      return 0;
    }
    ExclusiveAccess((uint *)(*param_1 + 0x14));
    bVar1 = (bool)hasExclusiveAccess((uint *)(*param_1 + 0x14));
    if (bVar1) {
      *(uint *)(*param_1 + 0x14) = *(uint *)(*param_1 + 0x14) | 0x80;
      return 0;
    }
    ExclusiveAccess((uint *)(*param_1 + 0x14));
    bVar1 = (bool)hasExclusiveAccess((uint *)(*param_1 + 0x14));
    if (bVar1) {
      *(uint *)(*param_1 + 0x14) = *(uint *)(*param_1 + 0x14) | 0x80;
      return 0;
    }
    ExclusiveAccess((uint *)(*param_1 + 0x14));
    bVar1 = (bool)hasExclusiveAccess((uint *)(*param_1 + 0x14));
  } while (!bVar1);
  *(uint *)(*param_1 + 0x14) = *(uint *)(*param_1 + 0x14) | 0x80;
  return 0;
}



/* 08005808 */

void HardFault_Handler(void)

{
  do {
                    /* WARNING: Do nothing block with infinite loop */
  } while( true );
}



/* 08005870 */

undefined4 FUN_08005870(undefined4 param_1,undefined1 *param_2,int param_3)

{
  int iVar1;
  
  FUN_08005c10();
  FUN_08005b58(param_1);
  iVar1 = FUN_08005d30();
  if (iVar1 != 0) {
    return 1;
  }
  while( true ) {
    if (param_3 == 0) {
      FUN_08005ca0(0);
      return 0;
    }
    FUN_08005b58(*param_2);
    iVar1 = FUN_08005d30();
    if (iVar1 != 0) break;
    param_3 = param_3 + -1;
    param_2 = param_2 + 1;
  }
  FUN_08005ca0();
  return 1;
}



/* 080058b8 */

undefined4 FUN_080058b8(undefined4 param_1,undefined4 param_2,undefined1 *param_3,int param_4)

{
  int iVar1;
  
  FUN_08005c10();
  FUN_08005b58(param_1);
  iVar1 = FUN_08005d30();
  if (iVar1 == 0) {
    FUN_08005b58(param_2);
    iVar1 = FUN_08005d30();
    if (iVar1 == 0) {
      while( true ) {
        if (param_4 == 0) {
          FUN_08005ca0();
          return 0;
        }
        FUN_08005b58(*param_3);
        iVar1 = FUN_08005d30();
        if (iVar1 != 0) break;
        param_4 = param_4 + -1;
        param_3 = param_3 + 1;
      }
      FUN_08005ca0();
      return 1;
    }
  }
  return 1;
}



/* 08005918 */

void FUN_08005918(void)

{
  uint uVar1;
  undefined4 local_24;
  undefined4 local_20;
  undefined4 uStack_1c;
  undefined4 local_18;
  undefined4 local_14;
  
  FUN_08001f84(0x40020400,0x400,0);
  local_24 = 0x800;
  local_20 = 1;
  uStack_1c = 0;
  local_18 = 3;
  local_14 = 0;
  FUN_08001dd8(0x40020400,&local_24);
  FUN_08001f84(0x40020400,0x800,0);
  local_24 = 2;
  uVar1 = 0;
  do {
    uVar1 = uVar1 + 1;
  } while (uVar1 < 0xe);
  FUN_08001f84(0x40020400,0x400,1);
  local_24 = 2;
  uVar1 = 0;
  do {
    uVar1 = uVar1 + 1;
  } while (uVar1 < 0xe);
  FUN_08001f84(0x40020400,0x400,0);
  return;
}



/* 080059a8 */

void FUN_080059a8(void)

{
  undefined4 local_2c;
  undefined4 local_28;
  undefined4 local_24;
  undefined4 local_20;
  undefined4 local_1c;
  
  local_2c = 0x800;
  local_1c = 0;
  local_28 = 1;
  local_24 = 0;
  local_20 = 3;
  FUN_08001dd8(0x40020400,&local_2c);
  local_2c = 0x400;
  local_28 = 1;
  local_24 = 0;
  local_20 = 3;
  FUN_08001dd8(0x40020400,&local_2c);
  FUN_08001f84(0x40020400,0x800,1);
  FUN_08001f84(0x40020400,0x400,1);
  return;
}



/* 08005a08 */

void FUN_08005a08(void)

{
  uint uVar1;
  undefined4 local_24;
  undefined4 local_20;
  undefined4 uStack_1c;
  undefined4 local_18;
  undefined4 local_14;
  
  FUN_08001f84(0x40020400,0x400,0);
  local_24 = 0x800;
  local_20 = 1;
  uStack_1c = 0;
  local_18 = 3;
  local_14 = 0;
  FUN_08001dd8(0x40020400,&local_24);
  FUN_08001f84(0x40020400,0x800,1);
  local_24 = 2;
  uVar1 = 0;
  do {
    uVar1 = uVar1 + 1;
  } while (uVar1 < 0xe);
  FUN_08001f84(0x40020400,0x400,1);
  local_24 = 2;
  uVar1 = 0;
  do {
    uVar1 = uVar1 + 1;
  } while (uVar1 < 0xe);
  FUN_08001f84(0x40020400,0x400,0);
  return;
}



/* 08005a98 */

byte FUN_08005a98(int param_1)

{
  uint uVar1;
  int iVar2;
  byte bVar3;
  uint uVar4;
  bool bVar5;
  undefined4 local_30;
  undefined4 uStack_2c;
  undefined4 local_28;
  undefined4 local_24;
  undefined4 local_20;
  
  bVar3 = 0;
  local_30 = 0x800;
  uStack_2c = 0;
  local_24 = 3;
  local_20 = 0;
  local_28 = 1;
  FUN_08001dd8(0x40020400,&local_30);
  uVar4 = 0;
  do {
    FUN_08001f84(0x40020400,0x400,0);
    local_30 = 2;
    uVar1 = 0;
    do {
      uVar1 = uVar1 + 1;
    } while (uVar1 < 0xe);
    FUN_08001f84(0x40020400,0x400,1);
    iVar2 = FUN_08001f78(0x40020400,0x800);
    local_30 = 1;
    uVar1 = 0;
    do {
      uVar1 = uVar1 + 1;
    } while (uVar1 < 7);
    bVar3 = iVar2 != 0 | bVar3 << 1;
    bVar5 = uVar4 < 7;
    uVar4 = uVar4 + 1;
  } while (bVar5);
  if (param_1 == 0) {
    FUN_08005a08();
    return bVar3;
  }
  FUN_08005918();
  return bVar3;
}



/* 08005b58 */

void FUN_08005b58(byte param_1)

{
  uint uVar1;
  uint uVar2;
  bool bVar3;
  undefined4 local_28;
  undefined4 local_24;
  undefined4 uStack_20;
  undefined4 local_1c;
  undefined4 local_18;
  
  uVar2 = 0;
  local_28 = 0x800;
  local_24 = 1;
  uStack_20 = 0;
  local_1c = 3;
  local_18 = 0;
  FUN_08001dd8(0x40020400,&local_28);
  FUN_08001f84(0x40020400,0x400,0);
  do {
    FUN_08001f84(0x40020400,0x800,param_1 >> 7);
    local_28 = 2;
    uVar1 = 0;
    do {
      uVar1 = uVar1 + 1;
    } while (uVar1 < 0xe);
    FUN_08001f84(0x40020400,0x400,1);
    local_28 = 2;
    uVar1 = 0;
    do {
      uVar1 = uVar1 + 1;
    } while (uVar1 < 0xe);
    FUN_08001f84(0x40020400,0x400,0);
    local_28 = 2;
    uVar1 = 0;
    do {
      uVar1 = uVar1 + 1;
    } while (uVar1 < 0xe);
    param_1 = param_1 << 1;
    bVar3 = uVar2 < 7;
    uVar2 = uVar2 + 1;
  } while (bVar3);
  return;
}



/* 08005c10 */

void FUN_08005c10(void)

{
  uint uVar1;
  undefined4 local_24;
  undefined4 local_20;
  undefined4 uStack_1c;
  undefined4 local_18;
  undefined4 local_14;
  
  local_24 = 0x800;
  local_14 = 0;
  local_20 = 1;
  uStack_1c = 0;
  local_18 = 3;
  FUN_08001dd8(0x40020400,&local_24);
  FUN_08001f84(0x40020400,0x800,1);
  FUN_08001f84(0x40020400,0x400,1);
  local_24 = 4;
  uVar1 = 0;
  do {
    uVar1 = uVar1 + 1;
  } while (uVar1 < 0x1c);
  FUN_08001f84(0x40020400,0x800,0);
  local_24 = 4;
  uVar1 = 0;
  do {
    uVar1 = uVar1 + 1;
  } while (uVar1 < 0x1c);
  FUN_08001f84(0x40020400,0x400,0);
  return;
}



/* 08005ca0 */

void FUN_08005ca0(void)

{
  uint uVar1;
  undefined4 local_24;
  undefined4 local_20;
  undefined4 uStack_1c;
  undefined4 local_18;
  undefined4 local_14;
  
  local_24 = 0x800;
  local_14 = 0;
  local_20 = 1;
  uStack_1c = 0;
  local_18 = 3;
  FUN_08001dd8(0x40020400,&local_24);
  FUN_08001f84(0x40020400,0x400,0);
  FUN_08001f84(0x40020400,0x800,0);
  local_24 = 4;
  uVar1 = 0;
  do {
    uVar1 = uVar1 + 1;
  } while (uVar1 < 0x1c);
  FUN_08001f84(0x40020400,0x400,1);
  FUN_08001f84(0x40020400,0x800,1);
  uVar1 = 0;
  do {
    uVar1 = uVar1 + 1;
  } while (uVar1 < 0x1c);
  return;
}



/* 08005d30 */

undefined4 FUN_08005d30(void)

{
  uint uVar1;
  int iVar2;
  bool bVar3;
  undefined4 local_24;
  undefined4 uStack_20;
  undefined4 local_1c;
  undefined4 local_18;
  undefined4 local_14;
  
  local_14 = 0;
  local_24 = 0x800;
  uStack_20 = 0;
  local_18 = 3;
  local_1c = 1;
  FUN_08001dd8(0x40020400,&local_24);
  FUN_08001f84(0x40020400,0x800,1);
  local_24 = 1;
  uVar1 = 0;
  do {
    uVar1 = uVar1 + 1;
  } while (uVar1 < 7);
  FUN_08001f84(0x40020400,0x400,1);
  local_24 = 1;
  uVar1 = 0;
  do {
    uVar1 = uVar1 + 1;
  } while (uVar1 < 7);
  uVar1 = 0;
  do {
    iVar2 = FUN_08001f78(0x40020400,0x800);
    if (iVar2 == 0) {
      FUN_08001f84(0x40020400,0x400,0);
      return 0;
    }
    bVar3 = uVar1 < 0xfa;
    uVar1 = uVar1 + 1;
  } while (bVar3);
  FUN_08005ca0();
  return 1;
}



/* 08005dd4 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_08005dd4(void)

{
  int iVar1;
  undefined4 local_20;
  undefined4 local_1c;
  undefined4 local_18;
  undefined4 local_14;
  
  local_14 = 0;
  _DAT_2001cf5c = 0;
  _DAT_2001cf64 = 0xf000001;
  _DAT_2001cf68 = 0;
  _DAT_2001cf6c = 0;
  _DAT_2001cf3c = 0x40012000;
  _DAT_2001cf40 = 0x30000;
  _DAT_2001cf44 = 0;
  _DAT_2001cf48 = 0;
  _DAT_2001cf4c = 1;
  _DAT_2001cf50 = 0;
  _DAT_2001cf54 = 0;
  _DAT_2001cf58 = 2;
  iVar1 = FUN_08001560();
  if (iVar1 != 0) {
    FUN_08001414();
  }
  local_20 = 0x11;
  local_1c = 1;
  local_18 = 7;
  iVar1 = FUN_0800141c(&DAT_2001cf3c,&local_20);
  if (iVar1 != 0) {
    FUN_08001414();
  }
  local_20 = 8;
  local_1c = 2;
  iVar1 = FUN_0800141c(&DAT_2001cf3c,&local_20);
  if (iVar1 != 0) {
    FUN_08001414();
  }
  return;
}



/* 08005e60 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_08005e60(void)

{
  int iVar1;
  
  _DAT_2001cf84 = 0x40023000;
  iVar1 = FUN_08001908();
  if (iVar1 == 0) {
    return;
  }
  FUN_08001414();
  return;
}



/* 08005e88 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

uint FUN_08005e88(void)

{
  _DAT_40023830 = _DAT_40023830 | 0x600000;
  return _DAT_40023830 & 0x400000;
}



/* 08005ec0 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_08005ec0(void)

{
  _DAT_2001c1fc = FUN_0800d5c8(&DAT_08013594);
  _DAT_2001c200 = FUN_0800d6f0(1,0,&DAT_080135fc);
  _DAT_2001c204 = FUN_0800d6f0(1,0,&DAT_080135c8);
  _DAT_2001c208 = FUN_0800d6f0(1,0,&DAT_08013584);
  _DAT_2001c20c = FUN_0800d6f0(1,0,&DAT_08013648);
  _DAT_2001c210 = FUN_0800d6f0(1,0,&DAT_0801369c);
  _DAT_2001c214 = FUN_0800d6f0(1,0,&DAT_08013368);
  _DAT_2001c218 = FUN_0800d6f0(1,0,&DAT_0801368c);
  _DAT_2001c21c = FUN_0800d8a0(&LAB_0800bbd4_1,1,0,&DAT_08013390);
  _DAT_2001c220 = FUN_0800d8a0(&LAB_0800c424_1,1,0,&DAT_08013534);
  _DAT_2001c224 = FUN_0800d8a0(0x800c4d1,1,0,&DAT_0801355c);
  _DAT_2001c228 = FUN_0800d8a0(&LAB_0800bda8_1,1,0,&DAT_080133a0);
  _DAT_2001c22c = FUN_0800d8a0(&LAB_0800b78c_1,1,0,&DAT_08013334);
  _DAT_2001c230 = FUN_0800d45c(0x40,4,&DAT_0801360c);
  _DAT_2001c234 = FUN_0800d45c(0x10,0x20,&DAT_08013544);
  _DAT_2001c238 = FUN_0800d45c(0x20,1,&DAT_0801356c);
  _DAT_2001c23c = FUN_0800d45c(8,8,&DAT_08013378);
  _DAT_2001c240 = FUN_0800d80c(&DAT_08006ed5,0,&DAT_080134c8);
  _DAT_2001c244 = FUN_0800d80c(&LAB_0800c080_1,0,&DAT_08013510);
  _DAT_2001c248 = FUN_0800d80c(&LAB_0800e2dc_1,0,&DAT_08013624);
  _DAT_2001c24c = FUN_0800d80c(&LAB_0800dee4_1,0,&DAT_080135d8);
  _DAT_2001c250 = FUN_0800d80c(&LAB_0800f48c_1,0,&DAT_08013668);
  _DAT_2001c254 = FUN_0800d80c(&DAT_0800c075,0,&DAT_080134ec);
  _DAT_2001c258 = FUN_0800d80c(&DAT_0800b6f9,0,&DAT_08013310);
  _DAT_2001c25c = FUN_0800d80c(&LAB_0800b9a4_1,0,&DAT_08013344);
  _DAT_2001c260 = FUN_0800d80c(&LAB_0800d274_1,0,&DAT_080135a4);
  _DAT_2001c264 = FUN_0800d330(&DAT_08013658);
  return;
}



/* 08006108 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_08006108(void)

{
  uint uVar1;
  undefined4 extraout_r3;
  undefined4 uVar2;
  undefined4 local_38;
  undefined4 local_34;
  undefined4 local_30;
  undefined4 local_2c;
  undefined4 local_28;
  
  local_28 = 0;
  local_30 = 0;
  local_2c = 0;
  local_38 = 0;
  local_34 = 0;
  _DAT_40023830 = _DAT_40023830 | 0x9f;
  uVar1 = _DAT_40023830 & 8;
  FUN_08001f84(0x40021000,0x180,1);
  FUN_08001f84(0x40021000,0x400,0);
  FUN_08001f84(0x40020400,0xc00,0);
  uVar2 = 0x40020c00;
  FUN_08001f84(0x40020c00,0x5800,1,extraout_r3,0x40020c00,uVar1);
  FUN_08001f84(0x40020c00,0x2000,0);
  FUN_08001f84(0x40020800,0x100,1);
  FUN_08001f84(0x40020800,0x200,0);
  FUN_08001f84(0x40020000,0x1900,0);
  local_38 = 0x901c;
  local_34 = 3;
  local_30 = 0;
  FUN_08001dd8(0x40021000,&local_38);
  local_38 = 0xec37;
  local_34 = 3;
  local_30 = 0;
  FUN_08001dd8(0x40020800,&local_38);
  local_38 = 0xfc;
  local_34 = 3;
  local_30 = 0;
  FUN_08001dd8(0x40020000,&local_38);
  local_38 = 6;
  local_34 = 3;
  local_30 = 0;
  FUN_08001dd8(0x40020400,&local_38);
  local_38 = 0x180;
  local_34 = 1;
  local_30 = 0;
  local_2c = 3;
  FUN_08001dd8(0x40021000,&local_38);
  local_38 = 0x400;
  local_34 = 1;
  local_30 = 0;
  local_2c = 1;
  FUN_08001dd8(0x40021000,&local_38);
  local_38 = 0xc00;
  local_34 = 1;
  local_30 = 0;
  local_2c = 0;
  FUN_08001dd8(0x40020400,&local_38);
  local_38 = 0x1000;
  local_34 = 0x110000;
  local_30 = 2;
  FUN_08001dd8(0x40020400,&local_38);
  local_38 = 0x8493;
  local_34 = 3;
  local_30 = 0;
  FUN_08001dd8(uVar2,&local_38);
  local_38 = 0x7800;
  local_34 = 1;
  local_30 = 0;
  local_2c = 3;
  FUN_08001dd8(uVar2,&local_38);
  local_38 = 0x100;
  local_34 = 1;
  local_30 = 0;
  local_2c = 0;
  FUN_08001dd8(0x40020800,&local_38);
  local_38 = 0x200;
  local_34 = 1;
  local_30 = 0;
  local_2c = 2;
  FUN_08001dd8(0x40020800,&local_38);
  local_38 = 0x100;
  local_34 = 1;
  local_30 = 2;
  local_2c = 0;
  FUN_08001dd8(0x40020000,&local_38);
  local_38 = 0x1800;
  local_34 = 1;
  local_30 = 0;
  local_2c = 2;
  FUN_08001dd8(0x40020000,&local_38);
  local_38 = 8;
  local_34 = 0;
  local_30 = 0;
  FUN_08001dd8(uVar2,&local_38);
  local_38 = 3;
  local_34 = 0;
  local_30 = 0;
  FUN_08001dd8(0x40021000,&local_38);
  return;
}



/* 0800635c */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_0800635c(void)

{
  int iVar1;
  
  _DAT_2001d670 = 0x40003000;
  _DAT_2001d674 = 3;
  _DAT_2001d678 = 0x13;
  iVar1 = FUN_08002c18();
  if (iVar1 == 0) {
    return;
  }
  FUN_08001414();
  return;
}



/* 08006388 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_08006388(void)

{
  int iVar1;
  
  _DAT_2001d67c = 0x40003800;
  _DAT_2001d680 = 0x104;
  _DAT_2001d684 = 0;
  _DAT_2001d688 = 0;
  _DAT_2001d68c = 0;
  _DAT_2001d690 = 0;
  _DAT_2001d694 = 0x200;
  _DAT_2001d698 = 0;
  _DAT_2001d69c = 0;
  _DAT_2001d6a0 = 0;
  _DAT_2001d6a4 = 0;
  _DAT_2001d6a8 = 10;
  iVar1 = FUN_08003480();
  if (iVar1 == 0) {
    return;
  }
  FUN_08001414();
  return;
}



/* 080063d0 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_080063d0(void)

{
  int iVar1;
  undefined4 local_24;
  undefined4 local_20;
  undefined4 uStack_1c;
  undefined4 local_18;
  undefined4 local_14;
  undefined4 local_10;
  undefined4 uStack_c;
  
  local_10 = 0;
  uStack_c = 0;
  local_18 = 0;
  local_14 = 0;
  _DAT_2001d7dc = 0;
  _DAT_2001d7e0 = 999;
  _DAT_2001d7e4 = 0;
  _DAT_2001d7d4 = 0x40014400;
  _DAT_2001d7d8 = 0x347;
  _DAT_2001d7ec = 0x80;
  iVar1 = FUN_080037a0();
  if (iVar1 != 0) {
    FUN_08001414();
  }
  iVar1 = FUN_080046b4(&DAT_2001d7d4);
  if (iVar1 != 0) {
    FUN_08001414();
  }
  local_24 = 0x60;
  local_20 = 0;
  uStack_1c = 0;
  local_14 = 4;
  iVar1 = FUN_08004498(&DAT_2001d7d4,&local_24,0);
  if (iVar1 != 0) {
    FUN_08001414();
  }
  FUN_080040dc(&DAT_2001d7d4);
  return;
}



/* 0800645c */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_0800645c(void)

{
  int iVar1;
  undefined4 local_24;
  undefined4 local_20;
  undefined4 uStack_1c;
  undefined4 local_18;
  undefined4 local_14;
  undefined4 local_10;
  undefined4 uStack_c;
  
  local_10 = 0;
  uStack_c = 0;
  local_18 = 0;
  local_14 = 0;
  _DAT_2001d8b0 = 0;
  _DAT_2001d8b4 = 999;
  _DAT_2001d8b8 = 0;
  _DAT_2001d8a8 = 0x40014800;
  _DAT_2001d8ac = 0x347;
  _DAT_2001d8c0 = 0x80;
  iVar1 = FUN_080037a0();
  if (iVar1 != 0) {
    FUN_08001414();
  }
  iVar1 = FUN_080046b4(&DAT_2001d8a8);
  if (iVar1 != 0) {
    FUN_08001414();
  }
  local_24 = 0x60;
  local_20 = 0;
  uStack_1c = 0;
  local_14 = 4;
  iVar1 = FUN_08004498(&DAT_2001d8a8,&local_24,0);
  if (iVar1 != 0) {
    FUN_08001414();
  }
  FUN_080040dc(&DAT_2001d8a8);
  return;
}



/* 080064e8 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_080064e8(void)

{
  int iVar1;
  undefined4 local_34;
  undefined4 local_30;
  undefined4 local_2c;
  undefined4 uStack_28;
  undefined4 local_24;
  undefined4 uStack_20;
  undefined4 local_1c;
  undefined4 local_18;
  undefined4 local_14;
  undefined4 uStack_10;
  undefined4 local_c;
  
  local_c = 0;
  local_14 = 0;
  uStack_10 = 0;
  local_1c = 0;
  local_24 = 0;
  uStack_20 = 0;
  local_2c = 0;
  uStack_28 = 0;
  local_34 = 0;
  local_30 = 0;
  _DAT_2001d984 = 0;
  _DAT_2001d988 = 99;
  _DAT_2001d98c = 0;
  _DAT_2001d97c = 0x40001800;
  _DAT_2001d980 = 0x347;
  _DAT_2001d994 = 0x80;
  iVar1 = FUN_080037a0();
  if (iVar1 != 0) {
    FUN_08001414();
  }
  local_18 = 0x1000;
  iVar1 = FUN_08003a7c(&DAT_2001d97c,&local_18);
  if (iVar1 != 0) {
    FUN_08001414();
  }
  iVar1 = FUN_080043b0(&DAT_2001d97c);
  if (iVar1 != 0) {
    FUN_08001414();
  }
  local_34 = 0;
  local_30 = 0x32;
  local_24 = 0;
  local_2c = 2;
  iVar1 = FUN_080041fc(&DAT_2001d97c,&local_34,0);
  if (iVar1 != 0) {
    FUN_08001414();
  }
  return;
}



/* 08006590 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_08006590(void)

{
  int iVar1;
  undefined4 local_24;
  undefined4 uStack_20;
  undefined4 local_1c;
  undefined4 local_18;
  undefined4 local_14;
  undefined4 local_10;
  undefined4 uStack_c;
  
  local_10 = 0;
  uStack_c = 0;
  local_18 = 0;
  local_14 = 0;
  _DAT_2001da58 = 0;
  _DAT_2001da5c = 4999;
  _DAT_2001da60 = 0;
  _DAT_2001da50 = 0x40001c00;
  _DAT_2001da54 = 0x53;
  _DAT_2001da68 = 0x80;
  iVar1 = FUN_080037a0();
  if (iVar1 != 0) {
    FUN_08001414();
  }
  iVar1 = FUN_080043b0(&DAT_2001da50);
  if (iVar1 != 0) {
    FUN_08001414();
  }
  local_24 = 0;
  uStack_20 = 0;
  local_1c = 0;
  local_14 = 0;
  iVar1 = FUN_080041fc(&DAT_2001da50,&local_24,0);
  if (iVar1 != 0) {
    FUN_08001414();
  }
  *(uint *)(_DAT_2001da50 + 0x18) = *(uint *)(_DAT_2001da50 + 0x18) | 8;
  return;
}



/* 08006614 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_08006614(void)

{
  int iVar1;
  undefined4 local_5c;
  undefined4 uStack_58;
  undefined4 local_54;
  undefined4 uStack_50;
  undefined4 local_4c;
  undefined4 local_48;
  undefined4 local_44;
  undefined4 local_40;
  undefined4 local_3c;
  undefined4 uStack_38;
  undefined4 local_34;
  undefined4 uStack_30;
  undefined4 local_2c;
  undefined4 uStack_28;
  undefined4 local_24;
  undefined4 local_20;
  undefined4 local_1c;
  undefined4 local_18;
  undefined4 local_14;
  undefined4 uStack_10;
  undefined4 local_c;
  
  local_c = 0;
  local_14 = 0;
  uStack_10 = 0;
  local_1c = 0;
  local_24 = 0;
  local_20 = 0;
  local_2c = 0;
  uStack_28 = 0;
  local_34 = 0;
  uStack_30 = 0;
  local_3c = 0;
  uStack_38 = 0;
  local_44 = 0;
  local_40 = 0;
  local_4c = 0;
  local_48 = 0;
  local_54 = 0;
  uStack_50 = 0;
  local_5c = 0;
  uStack_58 = 0;
  _DAT_2001d700 = 0x40010000;
  _DAT_2001d704 = 0x347;
  _DAT_2001d708 = 0;
  _DAT_2001d70c = 999;
  _DAT_2001d710 = 0;
  _DAT_2001d714 = 0;
  _DAT_2001d718 = 0x80;
  iVar1 = FUN_080037a0();
  if (iVar1 != 0) {
    FUN_08001414();
  }
  local_18 = 0x1000;
  iVar1 = FUN_08003a7c(&DAT_2001d700,&local_18);
  if (iVar1 != 0) {
    FUN_08001414();
  }
  iVar1 = FUN_080046b4(&DAT_2001d700);
  if (iVar1 != 0) {
    FUN_08001414();
  }
  local_20 = 0;
  local_1c = 0;
  iVar1 = FUN_080036ec(&DAT_2001d700,&local_20);
  if (iVar1 != 0) {
    FUN_08001414();
  }
  local_3c = 0x60;
  uStack_38 = 0;
  local_2c = 4;
  uStack_28 = 0;
  local_34 = 0;
  uStack_30 = 0;
  local_24 = 0;
  iVar1 = FUN_08004498(&DAT_2001d700,&local_3c,0);
  if (iVar1 != 0) {
    FUN_08001414();
  }
  iVar1 = FUN_08004498(&DAT_2001d700,&local_3c,4);
  if (iVar1 != 0) {
    FUN_08001414();
  }
  iVar1 = FUN_08004498(&DAT_2001d700,&local_3c,8);
  if (iVar1 != 0) {
    FUN_08001414();
  }
  iVar1 = FUN_08004498(&DAT_2001d700,&local_3c,0xc);
  if (iVar1 != 0) {
    FUN_08001414();
  }
  local_4c = 0;
  local_54 = 0;
  uStack_50 = 0;
  local_5c = 0;
  uStack_58 = 0;
  local_40 = 0;
  local_48 = 0x2000;
  iVar1 = FUN_080036a4(&DAT_2001d700,&local_5c);
  if (iVar1 != 0) {
    FUN_08001414();
  }
  FUN_080040dc(&DAT_2001d700);
  return;
}



/* 08006770 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_08006770(void)

{
  int iVar1;
  undefined4 local_38;
  undefined4 uStack_34;
  undefined4 local_2c;
  undefined4 uStack_28;
  undefined4 local_24;
  undefined4 uStack_20;
  undefined4 local_1c;
  undefined4 uStack_18;
  undefined4 local_14;
  undefined4 uStack_10;
  undefined4 local_c;
  
  _DAT_2001dbf8 = 0x40000000;
  _DAT_2001dbfc = 0;
  _DAT_2001dc10 = 0x80;
  local_2c = 3;
  uStack_28 = 0;
  local_38 = 0;
  uStack_34 = 0;
  _DAT_2001dc00 = 0;
  _DAT_2001dc04 = 60000;
  _DAT_2001dc08 = 0;
  local_24 = 1;
  uStack_20 = 0;
  local_1c = 0;
  uStack_18 = 0;
  local_14 = 1;
  uStack_10 = 0;
  local_c = 0;
  iVar1 = FUN_08003c14(&DAT_2001dbf8,&local_2c);
  if (iVar1 != 0) {
    FUN_08001414();
  }
  iVar1 = FUN_080036ec(&DAT_2001dbf8,&local_38);
  if (iVar1 != 0) {
    FUN_08001414();
  }
  return;
}



/* 080067d8 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_080067d8(void)

{
  int iVar1;
  undefined4 local_38;
  undefined4 uStack_34;
  undefined4 local_2c;
  undefined4 uStack_28;
  undefined4 local_24;
  undefined4 uStack_20;
  undefined4 local_1c;
  undefined4 uStack_18;
  undefined4 local_14;
  undefined4 uStack_10;
  undefined4 local_c;
  
  _DAT_2001dccc = 0x40000400;
  _DAT_2001dcd0 = 0;
  _DAT_2001dce4 = 0x80;
  local_2c = 3;
  uStack_28 = 0;
  local_38 = 0;
  uStack_34 = 0;
  _DAT_2001dcd4 = 0;
  _DAT_2001dcd8 = 60000;
  _DAT_2001dcdc = 0;
  local_24 = 1;
  uStack_20 = 0;
  local_1c = 0;
  uStack_18 = 0;
  local_14 = 1;
  uStack_10 = 0;
  local_c = 0;
  iVar1 = FUN_08003c14(&DAT_2001dccc,&local_2c);
  if (iVar1 != 0) {
    FUN_08001414();
  }
  iVar1 = FUN_080036ec(&DAT_2001dccc,&local_38);
  if (iVar1 != 0) {
    FUN_08001414();
  }
  return;
}



/* 08006844 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_08006844(void)

{
  int iVar1;
  undefined4 local_38;
  undefined4 uStack_34;
  undefined4 local_2c;
  undefined4 uStack_28;
  undefined4 local_24;
  undefined4 uStack_20;
  undefined4 local_1c;
  undefined4 uStack_18;
  undefined4 local_14;
  undefined4 uStack_10;
  undefined4 local_c;
  
  _DAT_2001dda0 = 0x40000800;
  _DAT_2001dda4 = 0;
  _DAT_2001ddb8 = 0x80;
  local_2c = 3;
  uStack_28 = 0;
  local_38 = 0;
  uStack_34 = 0;
  _DAT_2001dda8 = 0;
  _DAT_2001ddac = 60000;
  _DAT_2001ddb0 = 0;
  local_24 = 1;
  uStack_20 = 0;
  local_1c = 0;
  uStack_18 = 0;
  local_14 = 1;
  uStack_10 = 0;
  local_c = 0;
  iVar1 = FUN_08003c14(&DAT_2001dda0,&local_2c);
  if (iVar1 != 0) {
    FUN_08001414();
  }
  iVar1 = FUN_080036ec(&DAT_2001dda0,&local_38);
  if (iVar1 != 0) {
    FUN_08001414();
  }
  return;
}



/* 080068b0 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_080068b0(void)

{
  int iVar1;
  undefined4 local_38;
  undefined4 uStack_34;
  undefined4 local_2c;
  undefined4 uStack_28;
  undefined4 local_24;
  undefined4 uStack_20;
  undefined4 local_1c;
  undefined4 uStack_18;
  undefined4 local_14;
  undefined4 uStack_10;
  undefined4 local_c;
  
  _DAT_2001de74 = 0x40000c00;
  _DAT_2001de78 = 0;
  _DAT_2001de8c = 0x80;
  local_2c = 3;
  uStack_28 = 0;
  local_38 = 0;
  uStack_34 = 0;
  _DAT_2001de7c = 0;
  _DAT_2001de80 = 60000;
  _DAT_2001de84 = 0;
  local_24 = 1;
  uStack_20 = 0;
  local_1c = 0;
  uStack_18 = 0;
  local_14 = 1;
  uStack_10 = 0;
  local_c = 0;
  iVar1 = FUN_08003c14(&DAT_2001de74,&local_2c);
  if (iVar1 != 0) {
    FUN_08001414();
  }
  iVar1 = FUN_080036ec(&DAT_2001de74,&local_38);
  if (iVar1 != 0) {
    FUN_08001414();
  }
  return;
}



/* 0800691c */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_0800691c(void)

{
  int iVar1;
  undefined4 local_10;
  undefined4 uStack_c;
  
  local_10 = 0;
  uStack_c = 0;
  _DAT_2001df50 = 0;
  _DAT_2001df54 = 9999;
  _DAT_2001df48 = 0x40001400;
  _DAT_2001df4c = 0x53;
  _DAT_2001df60 = 0x80;
  iVar1 = FUN_080037a0();
  if (iVar1 != 0) {
    FUN_08001414();
  }
  iVar1 = FUN_080036ec(&DAT_2001df48,&local_10);
  if (iVar1 != 0) {
    FUN_08001414();
  }
  return;
}



/* 08006970 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_08006970(void)

{
  int iVar1;
  undefined4 local_34;
  undefined4 local_30;
  undefined4 local_2c;
  undefined4 uStack_28;
  undefined4 local_24;
  undefined4 uStack_20;
  undefined4 local_1c;
  undefined4 local_18;
  undefined4 local_14;
  undefined4 uStack_10;
  undefined4 local_c;
  
  local_c = 0;
  local_14 = 0;
  uStack_10 = 0;
  local_1c = 0;
  local_24 = 0;
  uStack_20 = 0;
  local_2c = 0;
  uStack_28 = 0;
  local_34 = 0;
  local_30 = 0;
  _DAT_2001e024 = 0;
  _DAT_2001e028 = 999;
  _DAT_2001e02c = 0;
  _DAT_2001e01c = 0x40014000;
  _DAT_2001e020 = 0x347;
  _DAT_2001e034 = 0x80;
  iVar1 = FUN_080037a0();
  if (iVar1 != 0) {
    FUN_08001414();
  }
  local_18 = 0x1000;
  iVar1 = FUN_08003a7c(&DAT_2001e01c,&local_18);
  if (iVar1 != 0) {
    FUN_08001414();
  }
  iVar1 = FUN_080046b4(&DAT_2001e01c);
  if (iVar1 != 0) {
    FUN_08001414();
  }
  local_34 = 0x60;
  local_30 = 0;
  local_2c = 0;
  local_24 = 4;
  iVar1 = FUN_08004498(&DAT_2001e01c,&local_34,0);
  if (iVar1 != 0) {
    FUN_08001414();
  }
  iVar1 = FUN_08004498(&DAT_2001e01c,&local_34,4);
  if (iVar1 != 0) {
    FUN_08001414();
  }
  FUN_080040dc(&DAT_2001e01c);
  return;
}



/* 08006a3c */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_08006a3c(void)

{
  int iVar1;
  
  _DAT_2001e270 = 0x40005000;
  _DAT_2001e274 = 100000;
  _DAT_2001e278 = 0x1000;
  _DAT_2001e27c = 0x2000;
  _DAT_2001e280 = 0x400;
  _DAT_2001e284 = 4;
  _DAT_2001e288 = 0;
  _DAT_2001e28c = 0;
  iVar1 = FUN_08005244();
  if (iVar1 == 0) {
    return;
  }
  FUN_08001414();
  return;
}



/* 08006a84 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_08006a84(void)

{
  int iVar1;
  
  _DAT_2001e0f0 = 0x40011000;
  _DAT_2001e0f4 = 0x1c200;
  _DAT_2001e0f8 = 0;
  _DAT_2001e0fc = 0;
  _DAT_2001e100 = 0;
  _DAT_2001e104 = 0xc;
  _DAT_2001e108 = 0;
  _DAT_2001e10c = 0;
  iVar1 = FUN_08005244();
  if (iVar1 == 0) {
    return;
  }
  FUN_08001414();
  return;
}



/* 08006ac0 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_08006ac0(void)

{
  int iVar1;
  
  _DAT_2001e170 = 0x40004400;
  _DAT_2001e174 = 0x2580;
  _DAT_2001e178 = 0;
  _DAT_2001e17c = 0;
  _DAT_2001e180 = 0;
  _DAT_2001e184 = 0xc;
  _DAT_2001e188 = 0;
  _DAT_2001e18c = 0;
  iVar1 = FUN_08005244();
  if (iVar1 == 0) {
    return;
  }
  FUN_08001414();
  return;
}



/* 08006afc */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_08006afc(void)

{
  int iVar1;
  
  _DAT_2001e1f0 = 0x40004800;
  _DAT_2001e1f4 = 1000000;
  _DAT_2001e1f8 = 0;
  _DAT_2001e1fc = 0;
  _DAT_2001e200 = 0;
  _DAT_2001e204 = 0xc;
  _DAT_2001e208 = 0;
  _DAT_2001e20c = 0;
  iVar1 = FUN_08005244();
  if (iVar1 == 0) {
    return;
  }
  FUN_08001414();
  return;
}



/* 08006b3c */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_08006b3c(void)

{
  int iVar1;
  
  _DAT_2001e2f0 = 0x40011400;
  _DAT_2001e2f4 = 0x1c200;
  _DAT_2001e2f8 = 0;
  _DAT_2001e2fc = 0;
  _DAT_2001e300 = 0;
  _DAT_2001e304 = 0xc;
  _DAT_2001e308 = 0;
  _DAT_2001e30c = 0;
  iVar1 = FUN_08005244();
  if (iVar1 == 0) {
    return;
  }
  FUN_08001414();
  return;
}



/* 08006b78 */

void FUN_08006b78(void)

{
  int iVar1;
  
  iVar1 = FUN_08008be4(0x2001ca4c,&LAB_080094dc_1,0);
  if (iVar1 != 0) {
    FUN_08001414();
  }
  iVar1 = FUN_08009444(0x2001ca4c,0x2001c044);
  if (iVar1 != 0) {
    FUN_08001414();
  }
  iVar1 = FUN_080094c8(0x2001ca4c);
  if (iVar1 == 0) {
    return;
  }
  FUN_08001414();
  return;
}



/* 08006bd0 */

void MemManage_Handler(void)

{
  do {
                    /* WARNING: Do nothing block with infinite loop */
  } while( true );
}



/* 08006bd4 */

void NMI_Handler(void)

{
  FUN_080030b0();
  do {
                    /* WARNING: Do nothing block with infinite loop */
  } while( true );
}



/* 08006bdc */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void IRQ_77_Handler(void)

{
  char cVar1;
  int iVar2;
  int iVar3;
  uint uVar4;
  int iVar5;
  uint uVar6;
  undefined1 *puVar7;
  int iVar8;
  uint *puVar9;
  undefined4 uVar10;
  undefined4 uVar11;
  byte bVar12;
  int iVar13;
  uint uVar14;
  uint uVar15;
  bool bVar16;
  uint local_2c;
  
  iVar8 = _DAT_2001d24c;
  iVar2 = FUN_08009938(_DAT_2001d24c);
  if ((iVar2 == 1) && (iVar2 = FUN_0800a21c(_DAT_2001d24c), iVar2 != 0)) {
    iVar2 = FUN_0800a21c(_DAT_2001d24c);
    if (iVar2 << 10 < 0) {
      *(undefined4 *)(_DAT_2001d24c + 0x14) = 0x200000;
    }
    iVar2 = FUN_0800a21c();
    if (iVar2 << 0xb < 0) {
      *(undefined4 *)(_DAT_2001d24c + 0x14) = 0x100000;
    }
    iVar2 = FUN_0800a21c();
    if (iVar2 << 5 < 0) {
      *(undefined4 *)(_DAT_2001d24c + 0x14) = 0x4000000;
    }
    iVar2 = FUN_0800a21c();
    if (iVar2 << 0x1e < 0) {
      *(undefined4 *)(_DAT_2001d24c + 0x14) = 2;
    }
    iVar3 = FUN_0800a21c();
    iVar2 = _DAT_2001d24c;
    if ((iVar3 << 2 < 0) &&
       (*(undefined4 *)(_DAT_2001d24c + 0x14) = 0x20000000, (*(uint *)(iVar8 + 0x440) & 1) == 0)) {
      FUN_08009858(iVar8,0x10);
      FUN_08009798(iVar8);
      if (DAT_2001d255 == '\x02') {
        FUN_0800a1cc(_DAT_2001d24c,1);
      }
      FUN_08001fa4(&DAT_2001d24c);
      iVar2 = _DAT_2001d24c;
    }
    iVar3 = FUN_0800a21c(iVar2);
    iVar2 = _DAT_2001d24c;
    if (iVar3 << 7 < 0) {
      uVar4 = *(uint *)(_DAT_2001d24c + 0x440);
      local_2c = *(uint *)(_DAT_2001d24c + 0x440) & 0xffffffd1;
      if ((int)(uVar4 << 0x1e) < 0) {
        if ((uVar4 & 1) != 0) {
          FUN_08001f9c(&DAT_2001d24c);
        }
        local_2c = local_2c | 2;
      }
      if ((int)(uVar4 << 0x1c) < 0) {
        local_2c = local_2c | 8;
        if ((int)(uVar4 << 0x1d) < 0) {
          if (DAT_2001d255 == '\x02') {
            if ((uVar4 & 0x60000) == 0x40000) {
              uVar11 = 2;
            }
            else {
              uVar11 = 1;
            }
            FUN_0800a1cc(_DAT_2001d24c,uVar11);
          }
          else if (DAT_2001d253 == '\x01') {
            *(undefined4 *)(iVar2 + 0x404) = 60000;
          }
          FUN_08002ba8(&DAT_2001d24c);
        }
        else {
          FUN_08002ba0(&DAT_2001d24c);
        }
      }
      if ((int)(uVar4 << 0x1a) < 0) {
        local_2c = local_2c | 0x20;
      }
      *(uint *)(iVar2 + 0x440) = local_2c;
    }
    iVar3 = FUN_0800a21c(_DAT_2001d24c);
    iVar2 = _DAT_2001d24c;
    if (iVar3 << 0x1c < 0) {
      FUN_08002bb8(&DAT_2001d24c);
      iVar2 = _DAT_2001d24c;
      *(undefined4 *)(_DAT_2001d24c + 0x14) = 8;
    }
    iVar2 = FUN_0800a21c(iVar2);
    if (iVar2 << 6 < 0) {
      uVar4 = FUN_08009bec(_DAT_2001d24c);
      if (DAT_2001d251 != 0) {
        iVar2 = 0;
        uVar15 = 0;
        do {
          iVar3 = _DAT_2001d24c;
          if ((uVar4 >> (uVar15 & 0xf) & 1) == 0) goto switchD_0800235a_default;
          iVar13 = *(int *)(iVar8 + 0x500 + iVar2);
          uVar14 = uVar15 & 0xff;
          iVar5 = FUN_0800a20c(_DAT_2001d24c,uVar14);
          if (-1 < iVar13 << 0x10) {
            if (iVar5 * 0x20000000 < 0) {
              *(undefined4 *)(iVar2 + iVar3 + 0x508) = 4;
              puVar7 = &DAT_2001d24c + iVar2 * 2;
              uVar11 = 7;
LAB_080023de:
              iVar3 = _DAT_2001d24c;
              *(undefined4 *)(puVar7 + 0x50) = uVar11;
LAB_08002288:
              FUN_08009940(iVar3,uVar14);
              goto switchD_0800235a_default;
            }
            iVar5 = FUN_0800a20c(_DAT_2001d24c,uVar14);
            if (iVar5 << 0x1a < 0) {
              *(undefined4 *)(iVar2 + iVar3 + 0x508) = 0x20;
              iVar3 = iVar2 * 2;
              if (*(char *)(iVar3 + 0x2001d265) == '\x01') {
                *(undefined1 *)(iVar3 + 0x2001d265) = 0;
                iVar5 = _DAT_2001d24c;
                *(undefined4 *)(iVar3 + 0x2001d298) = 2;
                *(undefined4 *)(iVar3 + 0x2001d29c) = 3;
                FUN_08009940(iVar5,uVar14);
              }
              if ((*(char *)(iVar3 + 0x2001d266) == '\x01') &&
                 (*(char *)(iVar3 + 0x2001d267) == '\0')) {
                if (*(char *)(iVar3 + 0x2001d272) != '\x01') {
                  *(undefined1 *)(iVar3 + 0x2001d267) = 1;
                }
                iVar5 = _DAT_2001d24c;
                *(undefined4 *)(iVar3 + 0x2001d29c) = 3;
                FUN_08009940(iVar5,uVar14);
                *(undefined4 *)(iVar3 + 0x2001d290) = 0;
              }
              goto switchD_0800235a_default;
            }
            iVar5 = FUN_0800a20c(_DAT_2001d24c,uVar14);
            if (iVar5 << 0x16 < 0) {
              *(undefined4 *)(iVar2 + iVar3 + 0x508) = 0x200;
              iVar3 = _DAT_2001d24c;
              goto LAB_08002288;
            }
            uVar6 = FUN_0800a20c(_DAT_2001d24c,uVar14);
            iVar5 = _DAT_2001d24c;
            if ((uVar6 & 1) != 0) {
              iVar13 = iVar2 * 2;
              *(undefined4 *)(iVar13 + 0x2001d290) = 0;
              iVar5 = FUN_0800a20c(iVar5,uVar14);
              if (iVar5 << 0x19 < 0) {
                *(undefined1 *)(iVar13 + 0x2001d265) = 1;
                *(undefined4 *)(iVar2 + iVar3 + 0x508) = 0x40;
              }
              if (*(char *)(iVar13 + 0x2001d267) != '\0') {
                *(undefined1 *)(iVar13 + 0x2001d267) = 0;
                *(uint *)(iVar2 + iVar3 + 0x504) = *(uint *)(iVar2 + iVar3 + 0x504) & 0xfffeffff;
              }
              *(undefined4 *)(iVar2 + iVar3 + 0x508) = 1;
              iVar3 = _DAT_2001d24c;
              *(undefined4 *)(iVar13 + 0x2001d29c) = 1;
              goto LAB_08002288;
            }
            iVar5 = FUN_0800a20c(_DAT_2001d24c,uVar14);
            if (iVar5 << 0x19 < 0) {
              iVar5 = iVar2 * 2;
              *(undefined4 *)(iVar5 + 0x2001d29c) = 5;
              if (*(char *)(iVar5 + 0x2001d266) == '\0') {
                *(undefined1 *)(iVar5 + 0x2001d265) = 1;
              }
              iVar13 = _DAT_2001d24c;
              *(undefined4 *)(iVar5 + 0x2001d290) = 0;
              FUN_08009940(iVar13,uVar14);
              uVar11 = 0x40;
              goto LAB_08002542;
            }
            iVar5 = FUN_0800a20c(_DAT_2001d24c,uVar14);
            if (iVar5 << 0x1c < 0) {
              *(undefined4 *)(iVar2 + iVar3 + 0x508) = 8;
              puVar7 = &DAT_2001d24c + iVar2 * 2;
              uVar11 = 6;
              goto LAB_080023de;
            }
            iVar5 = FUN_0800a20c(_DAT_2001d24c,uVar14);
            if (iVar5 << 0x1b < 0) {
              iVar5 = iVar2 * 2;
              *(undefined4 *)(iVar5 + 0x2001d290) = 0;
              *(undefined4 *)(iVar5 + 0x2001d29c) = 4;
              if ((*(char *)(iVar5 + 0x2001d265) == '\0') && (*(char *)(iVar5 + 0x2001d264) == '\0')
                 ) {
                *(undefined1 *)(iVar5 + 0x2001d265) = 1;
              }
              FUN_08009940(_DAT_2001d24c,uVar14);
              uVar11 = 0x10;
              goto LAB_08002542;
            }
            iVar13 = FUN_0800a20c(_DAT_2001d24c,uVar14);
            iVar5 = _DAT_2001d24c;
            if (iVar13 << 0x18 < 0) {
              if (DAT_2001d252 == '\0') {
                *(undefined4 *)(iVar2 * 2 + 0x2001d29c) = 7;
                FUN_08009940(iVar5,uVar14);
              }
              else {
                iVar5 = iVar2 * 2;
                uVar6 = *(int *)(iVar5 + 0x2001d290) + 1;
                *(uint *)(iVar5 + 0x2001d290) = uVar6;
                if (uVar6 < 3) {
                  *(undefined4 *)(iVar5 + 0x2001d298) = 2;
                  *(uint *)(iVar2 + iVar3 + 0x500) =
                       *(uint *)(iVar2 + iVar3 + 0x500) & 0x3fffffff | 0x80000000;
                }
                else {
                  *(undefined4 *)(iVar5 + 0x2001d290) = 0;
                  *(undefined4 *)(iVar5 + 0x2001d298) = 4;
                  FUN_08002098(&DAT_2001d24c,uVar14,4);
                }
              }
              uVar11 = 0x80;
              goto LAB_08002542;
            }
            iVar13 = FUN_0800a20c(_DAT_2001d24c,uVar14);
            iVar5 = _DAT_2001d24c;
            if (iVar13 << 0x15 < 0) {
              *(undefined4 *)(iVar2 * 2 + 0x2001d29c) = 9;
              FUN_08009940(iVar5,uVar14);
              uVar11 = 0x400;
              goto LAB_08002542;
            }
            iVar5 = FUN_0800a20c(_DAT_2001d24c,uVar14);
            if (-1 < iVar5 << 0x1e) goto switchD_0800235a_default;
            iVar3 = iVar2 + iVar3;
            *(undefined4 *)(iVar3 + 0x508) = 2;
            iVar5 = iVar2 * 2;
            puVar7 = &DAT_2001d24c + iVar5;
            switch(*(undefined4 *)(iVar5 + 0x2001d29c)) {
            case 1:
              *(undefined4 *)(iVar5 + 0x2001d29c) = 2;
              uVar11 = 1;
              *(undefined4 *)(iVar5 + 0x2001d298) = 1;
              if ((*(byte *)(iVar5 + 0x2001d272) & 0xfe) == 2) {
                if (DAT_2001d252 == '\x01') {
                  if (*(int *)(iVar5 + 0x2001d280) != 0) {
                    if ((((*(int *)(iVar5 + 0x2001d280) + (uint)*(ushort *)(iVar5 + 0x2001d274)) - 1
                         ) / (uint)*(ushort *)(iVar5 + 0x2001d274) & 1) != 0) {
                      *(byte *)(iVar5 + 0x2001d289) = *(byte *)(iVar5 + 0x2001d289) ^ 1;
                    }
                    uVar11 = 1;
                  }
                }
                else if (DAT_2001d252 == '\0') {
                  *(byte *)(iVar5 + 0x2001d289) = *(byte *)(iVar5 + 0x2001d289) ^ 1;
                }
              }
              break;
            case 2:
            case 8:
              goto switchD_0800235a_default;
            case 3:
              *(undefined4 *)(iVar5 + 0x2001d29c) = 2;
              if (*(char *)(iVar5 + 0x2001d267) == '\x01') {
                uVar11 = 2;
                *(undefined4 *)(iVar5 + 0x2001d298) = 2;
                break;
              }
              goto switchD_08002640_default;
            case 4:
              uVar11 = 2;
              *(undefined4 *)(iVar5 + 0x2001d29c) = 2;
              *(undefined4 *)(iVar5 + 0x2001d298) = 2;
              if (*(char *)(iVar5 + 0x2001d267) == '\x01') {
                *(undefined1 *)(iVar5 + 0x2001d267) = 0;
                uVar11 = 2;
                *(uint *)(iVar3 + 0x504) = *(uint *)(iVar3 + 0x504) & 0xfffeffff;
              }
              break;
            case 5:
              uVar11 = 2;
              *(undefined4 *)(iVar5 + 0x2001d298) = 2;
              *(undefined4 *)(iVar5 + 0x2001d29c) = 2;
              break;
            case 6:
              uVar11 = 5;
              *(undefined4 *)(iVar5 + 0x2001d29c) = 2;
              *(undefined4 *)(iVar5 + 0x2001d298) = 5;
              break;
            case 7:
            case 9:
              uVar6 = *(int *)(iVar5 + 0x2001d290) + 1;
              *(undefined4 *)(iVar5 + 0x2001d29c) = 2;
              *(uint *)(iVar5 + 0x2001d290) = uVar6;
              if (uVar6 < 3) {
                uVar11 = 2;
                *(undefined4 *)(iVar5 + 0x2001d298) = 2;
                *(uint *)(iVar3 + 0x500) = *(uint *)(iVar3 + 0x500) & 0x3fffffff | 0x80000000;
              }
              else {
                uVar11 = 4;
                *(undefined4 *)(iVar5 + 0x2001d290) = 0;
                *(undefined4 *)(iVar5 + 0x2001d298) = 4;
              }
              break;
            default:
              goto switchD_0800235a_default;
            }
            goto LAB_080027e0;
          }
          if (iVar5 * 0x20000000 < 0) {
            uVar10 = 7;
            uVar11 = 4;
LAB_080024a0:
            *(undefined4 *)(iVar2 + iVar3 + 0x508) = uVar11;
            iVar5 = _DAT_2001d24c;
            *(undefined4 *)(iVar2 * 2 + 0x2001d29c) = uVar10;
            FUN_08009940(iVar5,uVar14);
          }
          else {
            iVar5 = FUN_0800a20c(_DAT_2001d24c,uVar14);
            if (iVar5 << 0x17 < 0) {
              uVar10 = 8;
              uVar11 = 0x100;
              goto LAB_080024a0;
            }
            iVar5 = FUN_0800a20c(_DAT_2001d24c,uVar14);
            if (iVar5 << 0x1c < 0) {
              uVar10 = 6;
              uVar11 = 8;
              goto LAB_080024a0;
            }
            iVar5 = FUN_0800a20c(_DAT_2001d24c,uVar14);
            if (iVar5 << 0x15 < 0) {
              uVar10 = 9;
              uVar11 = 0x400;
              goto LAB_080024a0;
            }
            iVar5 = FUN_0800a20c(_DAT_2001d24c,uVar14);
            if (iVar5 << 0x18 < 0) {
              uVar10 = 7;
              uVar11 = 0x80;
              goto LAB_080024a0;
            }
          }
          iVar5 = FUN_0800a20c(_DAT_2001d24c,uVar14);
          if (iVar5 << 0x16 < 0) {
            FUN_08009940(_DAT_2001d24c,uVar14);
            uVar11 = 0x200;
LAB_08002542:
            *(undefined4 *)(iVar2 + iVar3 + 0x508) = uVar11;
            goto switchD_0800235a_default;
          }
          uVar6 = FUN_0800a20c(_DAT_2001d24c,uVar14);
          if ((uVar6 & 1) != 0) {
            iVar3 = iVar2 + iVar3;
            *(undefined4 *)(iVar3 + 0x508) = 0x20;
            iVar5 = iVar2 * 2;
            if (*(char *)(iVar5 + 0x2001d267) == '\x01') {
              *(undefined1 *)(iVar5 + 0x2001d267) = 0;
              *(uint *)(iVar3 + 0x504) = *(uint *)(iVar3 + 0x504) & 0xfffeffff;
            }
            if (DAT_2001d252 != '\0') {
              *(uint *)(iVar5 + 0x2001d284) =
                   *(int *)(iVar5 + 0x2001d27c) - (*(uint *)(iVar3 + 0x510) & 0x7ffff);
            }
            *(undefined4 *)(iVar5 + 0x2001d29c) = 1;
            *(undefined4 *)(iVar5 + 0x2001d290) = 0;
            *(undefined4 *)(iVar3 + 0x508) = 1;
            switch(*(undefined1 *)(iVar5 + 0x2001d272)) {
            case 0:
            case 2:
              FUN_08009940(_DAT_2001d24c,uVar14);
              *(undefined4 *)(iVar3 + 0x508) = 0x10;
              break;
            case 1:
            case 3:
              *(uint *)(iVar3 + 0x500) = *(uint *)(iVar3 + 0x500) | 0x20000000;
              *(undefined4 *)(iVar5 + 0x2001d298) = 1;
              FUN_08002098(&DAT_2001d24c,uVar14,1);
            }
            if (DAT_2001d252 == '\x01') {
              if ((((*(int *)(iVar5 + 0x2001d284) + (uint)*(ushort *)(iVar5 + 0x2001d274)) - 1) /
                   (uint)*(ushort *)(iVar5 + 0x2001d274) & 1) != 0) {
                *(byte *)(iVar5 + 0x2001d288) = *(byte *)(iVar5 + 0x2001d288) ^ 1;
              }
            }
            else {
              *(byte *)(iVar5 + 0x2001d288) = *(byte *)(iVar5 + 0x2001d288) ^ 1;
            }
            goto switchD_0800235a_default;
          }
          iVar5 = FUN_0800a20c(_DAT_2001d24c,uVar14);
          if (iVar5 << 0x1a < 0) {
            *(undefined4 *)(iVar2 + iVar3 + 0x508) = 0x20;
            iVar3 = iVar2 * 2;
            puVar7 = &DAT_2001d24c + iVar3;
            if (*(char *)(iVar3 + 0x2001d266) == '\x01') {
              *(undefined1 *)(iVar3 + 0x2001d267) = 1;
              uVar11 = 3;
              goto LAB_080023de;
            }
            goto switchD_0800235a_default;
          }
          iVar5 = FUN_0800a20c(_DAT_2001d24c,uVar14);
          if (-1 < iVar5 << 0x1e) {
            iVar5 = FUN_0800a20c(_DAT_2001d24c,uVar14);
            if (iVar5 << 0x19 < 0) {
              *(undefined4 *)(iVar2 + iVar3 + 0x508) = 0x40;
              iVar5 = iVar2 * 2;
              *(undefined4 *)(iVar5 + 0x2001d29c) = 5;
              iVar3 = _DAT_2001d24c;
              if (*(char *)(iVar5 + 0x2001d266) == '\0') {
                *(undefined4 *)(iVar5 + 0x2001d290) = 0;
                iVar3 = _DAT_2001d24c;
              }
              goto LAB_08002288;
            }
            iVar5 = FUN_0800a20c(_DAT_2001d24c,uVar14);
            if (-1 < iVar5 << 0x1b) goto switchD_0800235a_default;
            iVar5 = iVar2 * 2;
            cVar1 = *(char *)(iVar5 + 0x2001d272);
            if (cVar1 == '\0' || cVar1 == '\x02') {
              bVar16 = DAT_2001d252 == '\0';
              *(undefined4 *)(iVar5 + 0x2001d290) = 0;
              if ((bVar16) || (*(char *)(iVar5 + 0x2001d267) == '\x01')) {
LAB_080027f4:
                iVar13 = _DAT_2001d24c;
                *(undefined4 *)(iVar5 + 0x2001d29c) = 4;
                FUN_08009940(iVar13,uVar14);
              }
            }
            else if (cVar1 == '\x03') {
              *(undefined4 *)(iVar5 + 0x2001d290) = 0;
              goto LAB_080027f4;
            }
            if (*(char *)(iVar5 + 0x2001d267) == '\x01') {
              *(undefined1 *)(iVar5 + 0x2001d267) = 0;
              iVar5 = iVar2 + iVar3;
              *(uint *)(iVar5 + 0x504) = *(uint *)(iVar5 + 0x504) & 0xfffeffff;
              *(uint *)(iVar5 + 0x50c) = *(uint *)(iVar5 + 0x50c) | 0x20;
            }
            *(undefined4 *)(iVar2 + iVar3 + 0x508) = 0x10;
            goto switchD_0800235a_default;
          }
          iVar3 = iVar2 + iVar3;
          *(undefined4 *)(iVar3 + 0x508) = 2;
          iVar5 = iVar2 * 2;
          puVar7 = &DAT_2001d24c + iVar5;
          switch(*(undefined4 *)(iVar5 + 0x2001d29c)) {
          case 1:
            *(undefined4 *)(iVar5 + 0x2001d29c) = 2;
            uVar11 = 1;
            goto LAB_080027dc;
          case 2:
            goto switchD_0800235a_default;
          case 3:
            *(undefined4 *)(iVar5 + 0x2001d29c) = 2;
            if (*(char *)(iVar5 + 0x2001d267) != '\x01') break;
            *(undefined4 *)(iVar5 + 0x2001d298) = 2;
            *(uint *)(iVar3 + 0x504) = *(uint *)(iVar3 + 0x504) | 0x10000;
            *(uint *)(iVar3 + 0x50c) = *(uint *)(iVar3 + 0x50c) | 0x40;
            *(uint *)(iVar3 + 0x50c) = *(uint *)(iVar3 + 0x50c) & 0xffffffdf;
            if ((*(byte *)(iVar5 + 0x2001d272) | 2) != 2) break;
            goto LAB_080027b2;
          case 4:
            bVar12 = *(byte *)(iVar5 + 0x2001d272);
            *(undefined4 *)(iVar5 + 0x2001d29c) = 2;
            goto LAB_080027a8;
          case 5:
            *(undefined4 *)(iVar5 + 0x2001d29c) = 2;
            if (*(char *)(iVar5 + 0x2001d267) == '\x01') {
              bVar12 = *(byte *)(iVar5 + 0x2001d272);
              if (bVar12 != 3) goto LAB_080027a8;
              uVar6 = *(int *)(iVar5 + 0x2001d294) + 1;
              *(uint *)(iVar5 + 0x2001d294) = uVar6;
              if (2 < uVar6) {
                *(undefined4 *)(iVar5 + 0x2001d294) = 0;
                *(undefined1 *)(iVar5 + 0x2001d267) = 0;
                if (*(uint *)(iVar5 + 0x2001d290) < 3) {
                  *(undefined1 *)(iVar5 + 0x2001d268) = 1;
                }
                goto LAB_08002676;
              }
              *(undefined4 *)(iVar5 + 0x2001d298) = 2;
            }
            break;
          case 6:
            *(undefined4 *)(iVar5 + 0x2001d29c) = 2;
            uVar11 = 5;
            goto LAB_080027dc;
          case 7:
          case 9:
            uVar6 = *(int *)(iVar5 + 0x2001d290) + 1;
            *(undefined4 *)(iVar5 + 0x2001d29c) = 2;
            *(uint *)(iVar5 + 0x2001d290) = uVar6;
            if (2 < uVar6) {
              *(undefined4 *)(iVar5 + 0x2001d290) = 0;
              if (*(char *)(iVar5 + 0x2001d266) == '\x01') {
                *(undefined2 *)(iVar5 + 0x2001d267) = 0;
LAB_08002676:
                *(uint *)(iVar3 + 0x504) = *(uint *)(iVar3 + 0x504) & 0xfffeffff;
              }
              goto LAB_080027da;
            }
            bVar12 = *(byte *)(iVar5 + 0x2001d272);
LAB_080027a8:
            *(undefined4 *)(iVar5 + 0x2001d298) = 2;
            if ((bVar12 | 2) == 2) {
LAB_080027b2:
              *(uint *)(iVar3 + 0x500) = *(uint *)(iVar3 + 0x500) & 0x3fffffff | 0x80000000;
            }
            break;
          case 8:
            *(undefined4 *)(iVar5 + 0x2001d29c) = 2;
            *(int *)(iVar5 + 0x2001d290) = *(int *)(iVar5 + 0x2001d290) + 1;
LAB_080027da:
            uVar11 = 4;
LAB_080027dc:
            *(undefined4 *)(iVar5 + 0x2001d298) = uVar11;
          }
switchD_08002640_default:
          uVar11 = *(undefined4 *)(puVar7 + 0x4c);
LAB_080027e0:
          FUN_08002098(&DAT_2001d24c,uVar14,uVar11);
switchD_0800235a_default:
          uVar15 = uVar15 + 1;
          iVar2 = iVar2 + 0x20;
        } while (uVar15 < DAT_2001d251);
      }
      *(undefined4 *)(_DAT_2001d24c + 0x14) = 0x2000000;
    }
    iVar2 = FUN_0800a21c();
    iVar8 = _DAT_2001d24c;
    if (iVar2 << 0x1b < 0) {
      *(uint *)(_DAT_2001d24c + 0x18) = *(uint *)(_DAT_2001d24c + 0x18) & 0xffffffef;
      uVar4 = *(uint *)(iVar8 + 0x20);
      if (((uVar4 & 0x1e0000) == 0x40000) && (uVar15 = (uVar4 & 0x7fff) >> 4, uVar15 != 0)) {
        iVar2 = (uVar4 & 0xf) * 0x40;
        if (*(int *)(iVar2 + 0x2001d278) != 0) {
          if (*(uint *)(iVar2 + 0x2001d280) < *(int *)(iVar2 + 0x2001d284) + uVar15) {
            *(undefined4 *)(iVar2 + 0x2001d298) = 4;
          }
          else {
            FUN_0800a224(iVar8,*(int *)(iVar2 + 0x2001d278),uVar15);
            *(uint *)(iVar2 + 0x2001d278) = *(int *)(iVar2 + 0x2001d278) + uVar15;
            *(uint *)(iVar2 + 0x2001d284) = *(int *)(iVar2 + 0x2001d284) + uVar15;
            iVar8 = iVar8 + (uVar4 & 0xf) * 0x20;
            if ((uVar15 == *(ushort *)(iVar2 + 0x2001d274)) &&
               ((*(uint *)(iVar8 + 0x510) & 0x1ff80000) != 0)) {
              puVar9 = (uint *)(iVar8 + 0x500);
              *puVar9 = *puVar9 & 0x3fffffff | 0x80000000;
              *(byte *)(iVar2 + 0x2001d288) = *(byte *)(iVar2 + 0x2001d288) ^ 1;
            }
          }
        }
      }
      *(uint *)(_DAT_2001d24c + 0x18) = *(uint *)(_DAT_2001d24c + 0x18) | 0x10;
    }
  }
  return;
}



/* 08006bf0 */

int PendSV_Handler(void)

{
  bool bVar1;
  undefined4 *puVar2;
  undefined4 *puVar3;
  undefined4 *puVar4;
  int iVar5;
  undefined4 *puVar6;
  undefined4 unaff_r4;
  undefined4 unaff_r5;
  undefined4 unaff_r6;
  undefined4 unaff_r7;
  undefined4 unaff_r8;
  undefined4 unaff_r9;
  undefined4 unaff_r10;
  undefined4 unaff_r11;
  uint unaff_lr;
  int iVar7;
  undefined4 unaff_s16;
  undefined4 unaff_s17;
  undefined4 unaff_s18;
  undefined4 unaff_s19;
  undefined4 unaff_s20;
  undefined4 unaff_s21;
  undefined4 unaff_s22;
  undefined4 unaff_s23;
  undefined4 unaff_s24;
  undefined4 unaff_s25;
  undefined4 unaff_s26;
  undefined4 unaff_s27;
  undefined4 unaff_s28;
  undefined4 unaff_s29;
  undefined4 unaff_s30;
  undefined4 unaff_s31;
  
  puVar2 = DAT_08006c50;
  puVar3 = (undefined4 *)getProcessStackPointer();
  InstructionSynchronizationBarrier(0xf);
  puVar6 = (undefined4 *)*DAT_08006c50;
  puVar4 = puVar3;
  if ((unaff_lr & 0x10) == 0) {
    puVar4 = puVar3 + -0x10;
    *puVar4 = unaff_s16;
    puVar3[-0xf] = unaff_s17;
    puVar3[-0xe] = unaff_s18;
    puVar3[-0xd] = unaff_s19;
    puVar3[-0xc] = unaff_s20;
    puVar3[-0xb] = unaff_s21;
    puVar3[-10] = unaff_s22;
    puVar3[-9] = unaff_s23;
    puVar3[-8] = unaff_s24;
    puVar3[-7] = unaff_s25;
    puVar3[-6] = unaff_s26;
    puVar3[-5] = unaff_s27;
    puVar3[-4] = unaff_s28;
    puVar3[-3] = unaff_s29;
    puVar3[-2] = unaff_s30;
    puVar3[-1] = unaff_s31;
  }
  puVar4[-1] = unaff_lr;
  puVar4[-2] = unaff_r11;
  puVar4[-3] = unaff_r10;
  puVar4[-4] = unaff_r9;
  puVar4[-5] = unaff_r8;
  puVar4[-6] = unaff_r7;
  puVar4[-7] = unaff_r6;
  puVar4[-8] = unaff_r5;
  puVar4[-9] = unaff_r4;
  *puVar6 = puVar4 + -9;
  bVar1 = (bool)isCurrentModePrivileged();
  if (bVar1) {
    setBasePriority(0x50);
  }
  DataSynchronizationBarrier(0xf);
  InstructionSynchronizationBarrier(0xf);
  FUN_080119b0(0x50);
  bVar1 = (bool)isCurrentModePrivileged();
  if (bVar1) {
    setBasePriority(0);
  }
  iVar5 = *(int *)*puVar2;
  iVar7 = iVar5 + 0x24;
  if ((*(uint *)(iVar5 + 0x20) & 0x10) == 0) {
    iVar7 = iVar5 + 100;
  }
  bVar1 = (bool)isCurrentModePrivileged();
  if (bVar1) {
    setProcessStackPointer(iVar7);
  }
  InstructionSynchronizationBarrier(0xf);
  return iVar7;
}



/* 08006c54 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_08006c54(void)

{
  _DAT_2001c540 = 0;
  _DAT_2001c528 = 3;
  _DAT_2001c52c = 3;
  _DAT_2001c578 = s_Terminal_08013853;
  _DAT_2001c57c = 0x2001c381;
  _DAT_2001c538 = 0x400;
  _DAT_2001c53c = 0;
  _DAT_2001c530 = s_Terminal_08013853;
  _DAT_2001c534 = 0x2001c5c0;
  _DAT_2001c544 = 0;
  _DAT_2001c580 = 0x10;
  _DAT_2001c584 = 0;
  _DAT_2001c51f = 0x545452;
  uRam2001c51c = 0x5245;
  _DAT_2001c518 = 0x47474553;
  _DAT_2001c588 = 0;
  _DAT_2001c58c = 0;
  DAT_2001c51e = 0x20;
  return;
}



/* 08006ccc */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_08006ccc(undefined4 param_1,undefined4 param_2)

{
  bool bVar1;
  undefined4 uVar2;
  
  if (DAT_2001c518 == '\0') {
    _DAT_2001c540 = 0;
    _DAT_2001c528 = 3;
    _DAT_2001c52c = 3;
    _DAT_2001c530 = s_Terminal_08013853;
    _DAT_2001c534 = 0x2001c5c0;
    _DAT_2001c538 = 0x400;
    _DAT_2001c53c = 0;
    _DAT_2001c578 = s_Terminal_08013853;
    _DAT_2001c57c = 0x2001c381;
    _DAT_2001c544 = 0;
    _DAT_2001c580 = 0x10;
    _DAT_2001c584 = 0;
    _DAT_2001c51f = 0x545452;
    uRam2001c51c = 0x5245;
    DAT_2001c518 = 'S';
    uRam2001c519 = 0x4745;
    DAT_2001c51b = 0x47;
    _DAT_2001c588 = 0;
    _DAT_2001c58c = 0;
    DAT_2001c51e = 0x20;
  }
  uVar2 = 0;
  bVar1 = (bool)isCurrentModePrivileged();
  if (bVar1) {
    uVar2 = getBasePriority();
  }
  bVar1 = (bool)isCurrentModePrivileged();
  if (bVar1) {
    setBasePriority(0x20);
  }
  FUN_08006d68(param_1,param_2);
  bVar1 = (bool)isCurrentModePrivileged();
  if (bVar1) {
    setBasePriority(uVar2);
  }
  return;
}



/* 08006d68 */

uint FUN_08006d68(int param_1,int param_2,uint param_3)

{
  int iVar1;
  uint uVar2;
  uint uVar3;
  uint uVar4;
  uint uVar5;
  
  param_1 = param_1 * 0x18;
  iVar1 = *(int *)(&DAT_2001c544 + param_1);
  if (iVar1 == 2) {
    uVar2 = *(uint *)(&DAT_2001c53c + param_1);
    uVar4 = 0;
    do {
      uVar3 = *(uint *)(&DAT_2001c540 + param_1) + ~uVar2;
      uVar5 = *(int *)(&DAT_2001c538 + param_1) - uVar2;
      if (*(uint *)(&DAT_2001c540 + param_1) <= uVar2) {
        uVar3 = uVar3 + *(int *)(&DAT_2001c538 + param_1);
      }
      if (uVar3 < uVar5) {
        uVar5 = uVar3;
      }
      if (param_3 <= uVar5) {
        uVar5 = param_3;
      }
      FUN_080006aa(*(int *)(&DAT_2001c534 + param_1) + uVar2,param_2,uVar5);
      uVar3 = uVar5 + uVar2;
      param_3 = param_3 - uVar5;
      uVar4 = uVar4 + uVar5;
      param_2 = param_2 + uVar5;
      uVar2 = 0;
      if (uVar3 != *(uint *)(&DAT_2001c538 + param_1)) {
        uVar2 = uVar3;
      }
      *(uint *)(&DAT_2001c53c + param_1) = uVar2;
    } while (param_3 != 0);
    return uVar4;
  }
  if (iVar1 != 1) {
    if (iVar1 == 0) {
      uVar4 = *(uint *)(&DAT_2001c53c + param_1);
      uVar2 = *(uint *)(&DAT_2001c540 + param_1);
      if (uVar4 < uVar2) {
        uVar2 = uVar2 + ~uVar4;
      }
      else {
        uVar2 = uVar2 + ~uVar4 + *(int *)(&DAT_2001c538 + param_1);
      }
      if (param_3 <= uVar2) {
        uVar2 = *(int *)(&DAT_2001c538 + param_1) - uVar4;
        iVar1 = *(int *)(&DAT_2001c534 + param_1) + uVar4;
        if (param_3 < uVar2) {
          FUN_080006aa(iVar1,param_2,param_3);
          *(uint *)(&DAT_2001c53c + param_1) = uVar4 + param_3;
          return param_3;
        }
        goto LAB_08006e74;
      }
    }
    return 0;
  }
  uVar4 = *(uint *)(&DAT_2001c53c + param_1);
  uVar2 = *(uint *)(&DAT_2001c540 + param_1);
  if (uVar4 < uVar2) {
    iVar1 = *(int *)(&DAT_2001c538 + param_1);
    uVar2 = uVar2 + ~uVar4;
  }
  else {
    iVar1 = *(int *)(&DAT_2001c538 + param_1);
    uVar2 = uVar2 + ~uVar4 + iVar1;
  }
  if (uVar2 < param_3) {
    param_3 = uVar2;
  }
  uVar2 = iVar1 - uVar4;
  iVar1 = *(int *)(&DAT_2001c534 + param_1) + uVar4;
  if (param_3 < uVar2) {
    FUN_080006aa(iVar1,param_2,param_3);
    *(uint *)(&DAT_2001c53c + param_1) = param_3 + uVar4;
    return param_3;
  }
LAB_08006e74:
  FUN_080006aa(iVar1,param_2,uVar2);
  FUN_080006aa(*(undefined4 *)(&DAT_2001c534 + param_1),param_2 + uVar2,param_3 - uVar2);
  *(uint *)(&DAT_2001c53c + param_1) = param_3 - uVar2;
  return param_3;
}



/* 08006eb0 */

undefined4 SVC_Handler(void)

{
  bool bVar1;
  
  bVar1 = (bool)isCurrentModePrivileged();
  if (bVar1) {
    setProcessStackPointer(*(int *)*DAT_08006ed0 + 0x24);
  }
  InstructionSynchronizationBarrier(0xf);
  bVar1 = (bool)isCurrentModePrivileged();
  if (bVar1) {
    setBasePriority(0);
  }
  return 0;
}



/* 08006ee0 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined4 SysTick_Handler(void)

{
  bool bVar1;
  int iVar2;
  
  iVar2 = FUN_08012ce8(_DAT_e000e010);
  if (iVar2 == 1) {
    return 1;
  }
  bVar1 = (bool)isCurrentModePrivileged();
  if (bVar1) {
    setBasePriority(0x50);
  }
  InstructionSynchronizationBarrier(0xf);
  DataSynchronizationBarrier(0xf);
  iVar2 = FUN_08012d28(0x50);
  if (iVar2 != 0) {
    _DAT_e000ed04 = 0x10000000;
  }
  bVar1 = (bool)isCurrentModePrivileged();
  if (bVar1) {
    setBasePriority(0);
  }
  return 0;
}



/* 08006f00 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_08006f00(void)

{
  undefined4 uVar1;
  int iVar2;
  undefined4 extraout_r2;
  undefined4 extraout_r3;
  undefined4 local_54;
  undefined4 uStack_50;
  undefined4 local_4c;
  undefined4 local_48;
  undefined4 local_44;
  undefined4 local_40;
  undefined4 local_3c;
  undefined4 local_2c;
  undefined4 local_28;
  undefined4 local_24;
  undefined4 local_20;
  undefined4 local_1c;
  undefined4 uStack_18;
  undefined4 local_14;
  
  FUN_08000788(&local_40,0x30);
  local_44 = 0;
  local_4c = 0;
  local_48 = 0;
  local_54 = 0;
  uStack_50 = 0;
  _DAT_40023840 = _DAT_40023840 | 0x10000000;
  _DAT_40007000 = _DAT_40007000 | 0x4000;
  uVar1 = 0x4000;
  local_40 = 9;
  local_3c = 0x10000;
  local_2c = 1;
  local_24 = 0x400000;
  local_20 = 8;
  local_1c = 0xa8;
  uStack_18 = 2;
  local_14 = 7;
  local_28 = 2;
  iVar2 = FUN_080030cc(&local_40);
  if (iVar2 != 0) {
    disableIRQinterrupts();
    do {
                    /* WARNING: Do nothing block with infinite loop */
    } while( true );
  }
  local_54 = 0xf;
  uStack_50 = 2;
  local_48 = 0x1400;
  local_44 = 0x1000;
  local_4c = 0;
  iVar2 = FUN_08002e68(&local_54,5,extraout_r2,extraout_r3,uVar1);
  if (iVar2 != 0) {
    disableIRQinterrupts();
    do {
                    /* WARNING: Do nothing block with infinite loop */
    } while( true );
  }
  FUN_08002fcc();
  return;
}



/* 08006fb4 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_08006fb4(void)

{
  _DAT_e000ed88 = _DAT_e000ed88 | 0xf00000;
  _DAT_e000ed08 = 0x8000000;
  return;
}



/* 08006fd0 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void IRQ_28_Handler(void)

{
  int *piVar1;
  int iVar2;
  int iVar3;
  uint uVar4;
  uint uVar5;
  
  piVar1 = _DAT_2001dbf8;
  if ((_DAT_2001dbf8[4] & 1U) == 0) {
    return;
  }
  _DAT_2001dbf8[4] = -2;
  iVar2 = _DAT_2001e3ec;
  iVar3 = *piVar1;
  uVar5 = *(uint *)(_DAT_2001e3ec + 8);
  piVar1 = (int *)(_DAT_2001e3ec + 0xc);
  uVar4 = 0xffffffff;
  if (-1 < iVar3 << 0x1b) {
    uVar4 = 1;
  }
  *(uint *)(_DAT_2001e3ec + 8) = uVar4 + uVar5;
  *(uint *)(iVar2 + 0xc) = *piVar1 + ((iVar3 << 0x1b) >> 0x1f) + (uint)CARRY4(uVar4,uVar5);
  return;
}



/* 08007010 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void IRQ_29_Handler(void)

{
  int *piVar1;
  int iVar2;
  int iVar3;
  uint uVar4;
  uint uVar5;
  
  piVar1 = _DAT_2001dccc;
  if ((_DAT_2001dccc[4] & 1U) == 0) {
    return;
  }
  _DAT_2001dccc[4] = -2;
  iVar2 = _DAT_2001e3f4;
  iVar3 = *piVar1;
  uVar5 = *(uint *)(_DAT_2001e3f4 + 8);
  piVar1 = (int *)(_DAT_2001e3f4 + 0xc);
  uVar4 = 0xffffffff;
  if (-1 < iVar3 << 0x1b) {
    uVar4 = 1;
  }
  *(uint *)(_DAT_2001e3f4 + 8) = uVar4 + uVar5;
  *(uint *)(iVar2 + 0xc) = *piVar1 + ((iVar3 << 0x1b) >> 0x1f) + (uint)CARRY4(uVar4,uVar5);
  return;
}



/* 08007050 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void IRQ_30_Handler(void)

{
  int *piVar1;
  int iVar2;
  int iVar3;
  uint uVar4;
  uint uVar5;
  
  piVar1 = _DAT_2001dda0;
  if ((_DAT_2001dda0[4] & 1U) == 0) {
    return;
  }
  _DAT_2001dda0[4] = -2;
  iVar2 = _DAT_2001e3f0;
  iVar3 = *piVar1;
  uVar5 = *(uint *)(_DAT_2001e3f0 + 8);
  piVar1 = (int *)(_DAT_2001e3f0 + 0xc);
  uVar4 = 0xffffffff;
  if (-1 < iVar3 << 0x1b) {
    uVar4 = 1;
  }
  *(uint *)(_DAT_2001e3f0 + 8) = uVar4 + uVar5;
  *(uint *)(iVar2 + 0xc) = *piVar1 + ((iVar3 << 0x1b) >> 0x1f) + (uint)CARRY4(uVar4,uVar5);
  return;
}



/* 08007090 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void IRQ_50_Handler(void)

{
  int *piVar1;
  int iVar2;
  int iVar3;
  uint uVar4;
  uint uVar5;
  
  piVar1 = _DAT_2001de74;
  if ((_DAT_2001de74[4] & 1U) == 0) {
    return;
  }
  _DAT_2001de74[4] = -2;
  iVar2 = _DAT_2001e3e8;
  iVar3 = *piVar1;
  uVar5 = *(uint *)(_DAT_2001e3e8 + 8);
  piVar1 = (int *)(_DAT_2001e3e8 + 0xc);
  uVar4 = 0xffffffff;
  if (-1 < iVar3 << 0x1b) {
    uVar4 = 1;
  }
  *(uint *)(_DAT_2001e3e8 + 8) = uVar4 + uVar5;
  *(uint *)(iVar2 + 0xc) = *piVar1 + ((iVar3 << 0x1b) >> 0x1f) + (uint)CARRY4(uVar4,uVar5);
  return;
}



/* 080070d0 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void IRQ_55_Handler(void)

{
  undefined4 uVar1;
  
  if ((*(uint *)(_DAT_2001df48 + 0x10) & 1) == 0) {
    return;
  }
  *(undefined4 *)(_DAT_2001df48 + 0x10) = 0xfffffffe;
  uVar1 = DAT_0800718c;
  FUN_0800bfe0(DAT_0800718c,_DAT_2001e3e8,_DAT_2001de74,*(undefined4 *)(_DAT_2001de74 + 0x24),0);
  FUN_0800bfe0(uVar1,_DAT_2001e3ec,_DAT_2001dbf8,*(undefined4 *)(_DAT_2001dbf8 + 0x24),0);
  FUN_0800bfe0(uVar1,_DAT_2001e3f0,_DAT_2001dda0,*(undefined4 *)(_DAT_2001dda0 + 0x24),0);
  FUN_0800bfe0(uVar1,_DAT_2001e3f4,_DAT_2001dccc,*(undefined4 *)(_DAT_2001dccc + 0x24),0);
  FUN_0800befc(uVar1,_DAT_2001e3e8);
  FUN_0800befc(uVar1,_DAT_2001e3ec);
  FUN_0800befc(uVar1,_DAT_2001e3f0);
  FUN_0800befc(uVar1,_DAT_2001e3f4);
  return;
}



/* 08007190 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void IRQ_43_Handler(void)

{
  if ((*(uint *)(_DAT_2001d97c + 0x10) & 1) != 0) {
    *(undefined4 *)(_DAT_2001d97c + 0x10) = 0xfffffffe;
    FUN_08001f84(0x40020000,0x100,1);
  }
  if (-1 < *(int *)(_DAT_2001d97c + 0x10) << 0x1e) {
    return;
  }
  *(undefined4 *)(_DAT_2001d97c + 0x10) = 0xfffffffd;
  FUN_08001f84(0x40020000,0x100,0);
  return;
}



/* 080071dc */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void IRQ_45_Handler(void)

{
  code *UNRECOVERED_JUMPTABLE;
  code *pcVar1;
  int iVar2;
  uint uVar3;
  uint uVar4;
  
  iVar2 = _DAT_2001db24;
  uVar3 = *(uint *)(_DAT_2001db24 + 0xc);
  uVar4 = *(uint *)(_DAT_2001db24 + 0x10);
  if (((int)(uVar4 << 0x1e) < 0) && ((uVar3 & 2) != 0)) {
    *(undefined4 *)(_DAT_2001db24 + 0x10) = 0xfffffffd;
    _DAT_2001db40 = 1;
    if ((*(uint *)(iVar2 + 0x18) & 3) == 0) {
      (*_DAT_2001dbdc)(&DAT_2001db24);
      iVar2 = 0xbc;
    }
    else {
      iVar2 = 0xb0;
    }
    (**(code **)(&DAT_2001db24 + iVar2))(&DAT_2001db24);
    _DAT_2001db40 = 0;
  }
  iVar2 = _DAT_2001db24;
  if (((int)(uVar4 << 0x1d) < 0) && ((uVar3 & 4) != 0)) {
    *(undefined4 *)(_DAT_2001db24 + 0x10) = 0xfffffffb;
    _DAT_2001db40 = 2;
    if ((*(uint *)(iVar2 + 0x18) & 0x300) == 0) {
      (*_DAT_2001dbdc)(&DAT_2001db24);
      iVar2 = 0xbc;
    }
    else {
      iVar2 = 0xb0;
    }
    (**(code **)(&DAT_2001db24 + iVar2))(&DAT_2001db24);
    _DAT_2001db40 = 0;
  }
  iVar2 = _DAT_2001db24;
  if (((int)(uVar4 << 0x1c) < 0) && ((uVar3 & 8) != 0)) {
    *(undefined4 *)(_DAT_2001db24 + 0x10) = 0xfffffff7;
    _DAT_2001db40 = 4;
    if ((*(uint *)(iVar2 + 0x1c) & 3) == 0) {
      (*_DAT_2001dbdc)(&DAT_2001db24);
      iVar2 = 0xbc;
    }
    else {
      iVar2 = 0xb0;
    }
    (**(code **)(&DAT_2001db24 + iVar2))(&DAT_2001db24);
    _DAT_2001db40 = 0;
  }
  iVar2 = _DAT_2001db24;
  if (((int)(uVar4 << 0x1b) < 0) && ((uVar3 & 0x10) != 0)) {
    *(undefined4 *)(_DAT_2001db24 + 0x10) = 0xffffffef;
    _DAT_2001db40 = 8;
    if ((*(uint *)(iVar2 + 0x1c) & 0x300) == 0) {
      (*_DAT_2001dbdc)(&DAT_2001db24);
      iVar2 = 0xbc;
    }
    else {
      iVar2 = 0xb0;
    }
    (**(code **)(&DAT_2001db24 + iVar2))(&DAT_2001db24);
    _DAT_2001db40 = 0;
  }
  pcVar1 = _DAT_2001dbc4;
  UNRECOVERED_JUMPTABLE = _DAT_2001dbf4;
  if ((uVar4 & 1) != 0 && (uVar3 & 1) != 0) {
    *(undefined4 *)(_DAT_2001db24 + 0x10) = 0xfffffffe;
    (*pcVar1)(&DAT_2001db24);
    UNRECOVERED_JUMPTABLE = _DAT_2001dbf4;
  }
  _DAT_2001dbf4 = UNRECOVERED_JUMPTABLE;
  if (((int)(uVar4 << 0x18) < 0) && ((uVar3 & 0x80) != 0)) {
    *(undefined4 *)(_DAT_2001db24 + 0x10) = 0xffffff7f;
    (*UNRECOVERED_JUMPTABLE)(&DAT_2001db24);
  }
  UNRECOVERED_JUMPTABLE = _DAT_2001dbcc;
  if (((int)(uVar4 << 0x19) < 0) && ((uVar3 & 0x40) != 0)) {
    *(undefined4 *)(_DAT_2001db24 + 0x10) = 0xffffffbf;
    (*UNRECOVERED_JUMPTABLE)(&DAT_2001db24);
  }
  UNRECOVERED_JUMPTABLE = _DAT_2001dbec;
  if ((int)(uVar4 << 0x1a) < 0) {
    if ((uVar3 & 0x20) == 0) {
      return;
    }
    *(undefined4 *)(_DAT_2001db24 + 0x10) = 0xffffffdf;
                    /* WARNING: Could not recover jumptable at 0x080040d6. Too many branches */
                    /* WARNING: Treating indirect jump as call */
    (*UNRECOVERED_JUMPTABLE)(&DAT_2001db24);
    return;
  }
  return;
}



/* 080071e8 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void IRQ_44_Handler(void)

{
  int iVar1;
  
  iVar1 = _DAT_2001c4f0;
  if (*(int *)(_DAT_2001da50 + 0x10) << 0x1e < 0) {
    *(undefined4 *)(_DAT_2001da50 + 0x10) = 0xfffffffd;
    (**(code **)(*(int *)(_DAT_2001c4f0 * 4 + 0x2001e900) + 0x24))(0);
    iVar1 = 0;
    if (_DAT_2001c4f0 != 3) {
      iVar1 = _DAT_2001c4f0 + 1;
    }
  }
  _DAT_2001c4f0 = iVar1;
  if ((*(uint *)(_DAT_2001da50 + 0x10) & 1) != 0) {
    *(undefined4 *)(_DAT_2001da50 + 0x10) = 0xfffffffe;
    (**(code **)(*(int *)(_DAT_2001c4f0 * 4 + 0x2001e900) + 0x24))(1);
    FUN_0800f104(*(undefined4 *)(_DAT_2001c4f0 * 4 + 0x2001e900));
    *(undefined4 *)(_DAT_2001da50 + 0x34) =
         *(undefined4 *)(*(int *)(_DAT_2001c4f0 * 4 + 0x2001e900) + 0x10);
    return;
  }
  return;
}



/* 0800725c */

void FUN_0800725c(uint *param_1,uint *param_2)

{
  uint *puVar1;
  uint uVar2;
  uint uVar3;
  uint uVar4;
  
  uVar2 = *param_1;
  if ((int)param_1 < 0x40000c00) {
    if (((param_1 != (uint *)0x40000000) && (param_1 != (uint *)0x40000400)) &&
       (param_1 != (uint *)0x40000800)) goto LAB_08007292;
LAB_080072da:
    uVar2 = uVar2 & 0xffffff8f | param_2[1];
    if (0x40001fff < (int)param_1) goto LAB_080072ee;
LAB_0800729e:
    if ((int)param_1 < 0x40000c00) {
      if ((param_1 != (uint *)0x40000000) && (param_1 != (uint *)0x40000400)) {
        puVar1 = (uint *)0x40000800;
LAB_0800735c:
        if (param_1 != puVar1) goto LAB_08007368;
      }
    }
    else if ((param_1 != (uint *)0x40000c00) && (param_1 != (uint *)0x40001800)) {
      puVar1 = (uint *)0x40001c00;
      goto LAB_0800735c;
    }
  }
  else {
    if (((param_1 == (uint *)0x40000c00) || (param_1 == (uint *)0x40010400)) ||
       (param_1 == (uint *)0x40010000)) goto LAB_080072da;
LAB_08007292:
    if ((int)param_1 < 0x40002000) goto LAB_0800729e;
LAB_080072ee:
    if (0x40013fff < (int)param_1) {
      if ((param_1 == (uint *)0x40014000) || (param_1 == (uint *)0x40014800)) goto LAB_08007360;
      puVar1 = (uint *)0x40014400;
      goto LAB_0800735c;
    }
    if (((param_1 != (uint *)0x40002000) && (param_1 != (uint *)0x40010000)) &&
       (param_1 != (uint *)0x40010400)) goto LAB_08007368;
  }
LAB_08007360:
  uVar2 = uVar2 & 0xfffffcff | param_2[3];
LAB_08007368:
  uVar4 = *param_2;
  uVar3 = param_2[2];
  *param_1 = uVar2 & 0xffffff7f | param_2[5];
  param_1[0xb] = uVar3;
  param_1[10] = uVar4;
  if (((uint)param_1 | 0x400) == 0x40010400) {
    param_1[0xc] = param_2[4];
  }
  param_1[5] = 1;
  if ((param_1[4] & 1) == 0) {
    return;
  }
  param_1[4] = param_1[4] & 0xfffffffe;
  return;
}



/* 080073a0 */

void FUN_080073a0(void)

{
  undefined4 *puVar1;
  
  puVar1 = (undefined4 *)FUN_0800f094();
  if (puVar1 == (undefined4 *)0x0) {
    return;
  }
                    /* WARNING: Could not recover jumptable at 0x080073b4. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*(code *)*puVar1)(puVar1[1]);
  return;
}



/* 080073b8 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void IRQ_53_Handler(void)

{
  bool bVar1;
  ushort uVar2;
  uint *puVar3;
  int *piVar4;
  short sVar5;
  uint uVar6;
  uint uVar7;
  uint uVar8;
  uint uVar9;
  int iVar10;
  uint unaff_lr;
  
  puVar3 = _DAT_2001e270;
  uVar6 = *_DAT_2001e270;
  uVar8 = _DAT_2001e270[3];
  uVar7 = _DAT_2001e270[5];
  uVar9 = uVar8 & 0x20;
  if (((uVar6 & 0x2f) == 0x20) && (uVar9 != 0)) {
    FUN_08007774();
    return;
  }
  iVar10 = uVar6 * 0x10000000;
  if (iVar10 != 0) {
    unaff_lr = uVar7 & 1;
    uVar7 = uVar8 & 0x120;
  }
  if (iVar10 != 0 && uVar7 + unaff_lr != 0) {
    if ((uVar6 & 1) != 0 && (uVar8 & 0x100) != 0) {
      uRam2001e2bc = uRam2001e2bc | 1;
    }
    if (((int)(uVar6 << 0x1d) < 0) && (unaff_lr != 0)) {
      uRam2001e2bc = uRam2001e2bc | 2;
    }
    if (((int)(uVar6 << 0x1e) < 0) && (unaff_lr != 0)) {
      uRam2001e2bc = uRam2001e2bc | 4;
    }
    if ((iVar10 < 0) && (unaff_lr != 0 || uVar9 != 0)) {
      uRam2001e2bc = uRam2001e2bc | 8;
    }
    if (uRam2001e2bc != 0) {
      if (((int)(uVar6 << 0x1a) < 0) && (uVar9 != 0)) {
        FUN_08007774();
      }
      if ((_DAT_2001e270[5] & 0x40) + (uRam2001e2bc & 8) == 0) {
        (*pcRam2001e2d0)();
        uRam2001e2bc = 0;
        return;
      }
      do {
        ExclusiveAccess(_DAT_2001e270 + 3);
        bVar1 = (bool)hasExclusiveAccess(_DAT_2001e270 + 3);
        if (bVar1) {
          _DAT_2001e270[3] = _DAT_2001e270[3] & 0xfffffedf;
          goto LAB_0800502a;
        }
        ExclusiveAccess(_DAT_2001e270 + 3);
        bVar1 = (bool)hasExclusiveAccess(_DAT_2001e270 + 3);
        if (bVar1) {
          _DAT_2001e270[3] = _DAT_2001e270[3] & 0xfffffedf;
          goto LAB_0800502a;
        }
        ExclusiveAccess(_DAT_2001e270 + 3);
        bVar1 = (bool)hasExclusiveAccess(_DAT_2001e270 + 3);
        if (bVar1) {
          _DAT_2001e270[3] = _DAT_2001e270[3] & 0xfffffedf;
          goto LAB_0800502a;
        }
        ExclusiveAccess(_DAT_2001e270 + 3);
        bVar1 = (bool)hasExclusiveAccess(_DAT_2001e270 + 3);
      } while (!bVar1);
      _DAT_2001e270[3] = _DAT_2001e270[3] & 0xfffffedf;
LAB_0800502a:
      do {
        ExclusiveAccess(_DAT_2001e270 + 5);
        bVar1 = (bool)hasExclusiveAccess(_DAT_2001e270 + 5);
        if (bVar1) {
          _DAT_2001e270[5] = _DAT_2001e270[5] & 0xfffffffe;
          goto LAB_0800503e;
        }
        ExclusiveAccess(_DAT_2001e270 + 5);
        bVar1 = (bool)hasExclusiveAccess(_DAT_2001e270 + 5);
        if (bVar1) {
          _DAT_2001e270[5] = _DAT_2001e270[5] & 0xfffffffe;
          goto LAB_0800503e;
        }
        ExclusiveAccess(_DAT_2001e270 + 5);
        bVar1 = (bool)hasExclusiveAccess(_DAT_2001e270 + 5);
        if (bVar1) {
          _DAT_2001e270[5] = _DAT_2001e270[5] & 0xfffffffe;
          goto LAB_0800503e;
        }
        ExclusiveAccess(_DAT_2001e270 + 5);
        bVar1 = (bool)hasExclusiveAccess(_DAT_2001e270 + 5);
      } while (!bVar1);
      _DAT_2001e270[5] = _DAT_2001e270[5] & 0xfffffffe;
LAB_0800503e:
      if (iRam2001e2a0 == 1) {
        do {
          ExclusiveAccess(_DAT_2001e270 + 3);
          bVar1 = (bool)hasExclusiveAccess(_DAT_2001e270 + 3);
          if (bVar1) {
            _DAT_2001e270[3] = _DAT_2001e270[3] & 0xffffffef;
            goto LAB_0800508e;
          }
          ExclusiveAccess(_DAT_2001e270 + 3);
          bVar1 = (bool)hasExclusiveAccess(_DAT_2001e270 + 3);
          if (bVar1) {
            _DAT_2001e270[3] = _DAT_2001e270[3] & 0xffffffef;
            goto LAB_0800508e;
          }
          ExclusiveAccess(_DAT_2001e270 + 3);
          bVar1 = (bool)hasExclusiveAccess(_DAT_2001e270 + 3);
          if (bVar1) {
            _DAT_2001e270[3] = _DAT_2001e270[3] & 0xffffffef;
            goto LAB_0800508e;
          }
          ExclusiveAccess(_DAT_2001e270 + 3);
          bVar1 = (bool)hasExclusiveAccess(_DAT_2001e270 + 3);
        } while (!bVar1);
        _DAT_2001e270[3] = _DAT_2001e270[3] & 0xffffffef;
      }
LAB_0800508e:
      uRam2001e2b8 = 0x20;
      iRam2001e2a0 = 0;
      if ((int)(_DAT_2001e270[5] << 0x19) < 0) {
        do {
          ExclusiveAccess(_DAT_2001e270 + 5);
          bVar1 = (bool)hasExclusiveAccess(_DAT_2001e270 + 5);
          if (bVar1) {
            _DAT_2001e270[5] = _DAT_2001e270[5] & 0xffffffbf;
            goto LAB_080050ea;
          }
          ExclusiveAccess(_DAT_2001e270 + 5);
          bVar1 = (bool)hasExclusiveAccess(_DAT_2001e270 + 5);
          if (bVar1) {
            _DAT_2001e270[5] = _DAT_2001e270[5] & 0xffffffbf;
            goto LAB_080050ea;
          }
          ExclusiveAccess(_DAT_2001e270 + 5);
          bVar1 = (bool)hasExclusiveAccess(_DAT_2001e270 + 5);
          if (bVar1) {
            _DAT_2001e270[5] = _DAT_2001e270[5] & 0xffffffbf;
            goto LAB_080050ea;
          }
          ExclusiveAccess(_DAT_2001e270 + 5);
          bVar1 = (bool)hasExclusiveAccess(_DAT_2001e270 + 5);
        } while (!bVar1);
        _DAT_2001e270[5] = _DAT_2001e270[5] & 0xffffffbf;
LAB_080050ea:
        piVar4 = piRam2001e2ac;
        if (piRam2001e2ac != (int *)0x0) {
          piRam2001e2ac[0x15] = (int)&LAB_080073c4_1;
          iVar10 = FUN_080019e8(piVar4);
          if (iVar10 == 0) {
            return;
          }
                    /* WARNING: Could not recover jumptable at 0x08005114. Too many branches */
                    /* WARNING: Treating indirect jump as call */
          (*(code *)piRam2001e2ac[0x15])();
          return;
        }
      }
                    /* WARNING: Could not recover jumptable at 0x08005230. Too many branches */
                    /* WARNING: Treating indirect jump as call */
      (*pcRam2001e2d0)();
      return;
    }
  }
  else if ((((int)(uVar6 << 0x1b) < 0) && (iRam2001e2a0 == 1)) && ((uVar8 & 0x10) != 0)) {
    if ((int)(_DAT_2001e270[5] << 0x19) < 0) {
      sVar5 = (short)*(uint *)(*piRam2001e2ac + 4);
      uVar7 = *(uint *)(*piRam2001e2ac + 4) & 0xffff;
      if ((uVar7 != 0) && (uVar7 < uRam2001e29c)) {
        uRam2001e29e = sVar5;
        if (piRam2001e2ac[7] != 0x100) {
          do {
            ExclusiveAccess(_DAT_2001e270 + 3);
            bVar1 = (bool)hasExclusiveAccess(_DAT_2001e270 + 3);
            if (bVar1) {
              _DAT_2001e270[3] = _DAT_2001e270[3] & 0xfffffeff;
              goto LAB_08004e30;
            }
            ExclusiveAccess(_DAT_2001e270 + 3);
            bVar1 = (bool)hasExclusiveAccess(_DAT_2001e270 + 3);
            if (bVar1) {
              _DAT_2001e270[3] = _DAT_2001e270[3] & 0xfffffeff;
              goto LAB_08004e30;
            }
            ExclusiveAccess(_DAT_2001e270 + 3);
            bVar1 = (bool)hasExclusiveAccess(_DAT_2001e270 + 3);
            if (bVar1) {
              _DAT_2001e270[3] = _DAT_2001e270[3] & 0xfffffeff;
              goto LAB_08004e30;
            }
            ExclusiveAccess(_DAT_2001e270 + 3);
            bVar1 = (bool)hasExclusiveAccess(_DAT_2001e270 + 3);
          } while (!bVar1);
          _DAT_2001e270[3] = _DAT_2001e270[3] & 0xfffffeff;
LAB_08004e30:
          do {
            ExclusiveAccess(_DAT_2001e270 + 5);
            bVar1 = (bool)hasExclusiveAccess(_DAT_2001e270 + 5);
            if (bVar1) {
              _DAT_2001e270[5] = _DAT_2001e270[5] & 0xfffffffe;
              goto LAB_08004eb2;
            }
            ExclusiveAccess(_DAT_2001e270 + 5);
            bVar1 = (bool)hasExclusiveAccess(_DAT_2001e270 + 5);
            if (bVar1) {
              _DAT_2001e270[5] = _DAT_2001e270[5] & 0xfffffffe;
              goto LAB_08004eb2;
            }
            ExclusiveAccess(_DAT_2001e270 + 5);
            bVar1 = (bool)hasExclusiveAccess(_DAT_2001e270 + 5);
            if (bVar1) {
              _DAT_2001e270[5] = _DAT_2001e270[5] & 0xfffffffe;
              goto LAB_08004eb2;
            }
            ExclusiveAccess(_DAT_2001e270 + 5);
            bVar1 = (bool)hasExclusiveAccess(_DAT_2001e270 + 5);
          } while (!bVar1);
          _DAT_2001e270[5] = _DAT_2001e270[5] & 0xfffffffe;
LAB_08004eb2:
          do {
            ExclusiveAccess(_DAT_2001e270 + 5);
            bVar1 = (bool)hasExclusiveAccess(_DAT_2001e270 + 5);
            if (bVar1) {
              _DAT_2001e270[5] = _DAT_2001e270[5] & 0xffffffbf;
              goto LAB_08004ec6;
            }
            ExclusiveAccess(_DAT_2001e270 + 5);
            bVar1 = (bool)hasExclusiveAccess(_DAT_2001e270 + 5);
            if (bVar1) {
              _DAT_2001e270[5] = _DAT_2001e270[5] & 0xffffffbf;
              goto LAB_08004ec6;
            }
            ExclusiveAccess(_DAT_2001e270 + 5);
            bVar1 = (bool)hasExclusiveAccess(_DAT_2001e270 + 5);
            if (bVar1) {
              _DAT_2001e270[5] = _DAT_2001e270[5] & 0xffffffbf;
              goto LAB_08004ec6;
            }
            ExclusiveAccess(_DAT_2001e270 + 5);
            bVar1 = (bool)hasExclusiveAccess(_DAT_2001e270 + 5);
          } while (!bVar1);
          _DAT_2001e270[5] = _DAT_2001e270[5] & 0xffffffbf;
LAB_08004ec6:
          uRam2001e2b8 = 0x20;
          iRam2001e2a0 = 0;
          do {
            ExclusiveAccess(_DAT_2001e270 + 3);
            bVar1 = (bool)hasExclusiveAccess(_DAT_2001e270 + 3);
            if (bVar1) {
              _DAT_2001e270[3] = _DAT_2001e270[3] & 0xffffffef;
              goto LAB_08004f18;
            }
            ExclusiveAccess(_DAT_2001e270 + 3);
            bVar1 = (bool)hasExclusiveAccess(_DAT_2001e270 + 3);
            if (bVar1) {
              _DAT_2001e270[3] = _DAT_2001e270[3] & 0xffffffef;
              goto LAB_08004f18;
            }
            ExclusiveAccess(_DAT_2001e270 + 3);
            bVar1 = (bool)hasExclusiveAccess(_DAT_2001e270 + 3);
            if (bVar1) {
              _DAT_2001e270[3] = _DAT_2001e270[3] & 0xffffffef;
              goto LAB_08004f18;
            }
            ExclusiveAccess(_DAT_2001e270 + 3);
            bVar1 = (bool)hasExclusiveAccess(_DAT_2001e270 + 3);
          } while (!bVar1);
          _DAT_2001e270[3] = _DAT_2001e270[3] & 0xffffffef;
LAB_08004f18:
          FUN_08001968(piRam2001e2ac);
        }
        uRam2001e2a4 = 2;
                    /* WARNING: Could not recover jumptable at 0x08004f38. Too many branches */
                    /* WARNING: Treating indirect jump as call */
        (*pcRam2001e2e4)(&DAT_2001e270,uRam2001e29c - uRam2001e29e);
        return;
      }
    }
    else if (uRam2001e29e != 0 && uRam2001e29c != uRam2001e29e) {
      sVar5 = uRam2001e29c - uRam2001e29e;
      do {
        ExclusiveAccess(_DAT_2001e270 + 3);
        bVar1 = (bool)hasExclusiveAccess(_DAT_2001e270 + 3);
        if (bVar1) {
          _DAT_2001e270[3] = _DAT_2001e270[3] & 0xfffffedf;
          goto LAB_080051ae;
        }
        ExclusiveAccess(_DAT_2001e270 + 3);
        bVar1 = (bool)hasExclusiveAccess(_DAT_2001e270 + 3);
        if (bVar1) {
          _DAT_2001e270[3] = _DAT_2001e270[3] & 0xfffffedf;
          goto LAB_080051ae;
        }
        ExclusiveAccess(_DAT_2001e270 + 3);
        bVar1 = (bool)hasExclusiveAccess(_DAT_2001e270 + 3);
        if (bVar1) {
          _DAT_2001e270[3] = _DAT_2001e270[3] & 0xfffffedf;
          goto LAB_080051ae;
        }
        ExclusiveAccess(_DAT_2001e270 + 3);
        bVar1 = (bool)hasExclusiveAccess(_DAT_2001e270 + 3);
      } while (!bVar1);
      _DAT_2001e270[3] = _DAT_2001e270[3] & 0xfffffedf;
LAB_080051ae:
      do {
        ExclusiveAccess(_DAT_2001e270 + 5);
        bVar1 = (bool)hasExclusiveAccess(_DAT_2001e270 + 5);
        if (bVar1) {
          _DAT_2001e270[5] = _DAT_2001e270[5] & 0xfffffffe;
          goto LAB_080051c2;
        }
        ExclusiveAccess(_DAT_2001e270 + 5);
        bVar1 = (bool)hasExclusiveAccess(_DAT_2001e270 + 5);
        if (bVar1) {
          _DAT_2001e270[5] = _DAT_2001e270[5] & 0xfffffffe;
          goto LAB_080051c2;
        }
        ExclusiveAccess(_DAT_2001e270 + 5);
        bVar1 = (bool)hasExclusiveAccess(_DAT_2001e270 + 5);
        if (bVar1) {
          _DAT_2001e270[5] = _DAT_2001e270[5] & 0xfffffffe;
          goto LAB_080051c2;
        }
        ExclusiveAccess(_DAT_2001e270 + 5);
        bVar1 = (bool)hasExclusiveAccess(_DAT_2001e270 + 5);
      } while (!bVar1);
      _DAT_2001e270[5] = _DAT_2001e270[5] & 0xfffffffe;
LAB_080051c2:
      uRam2001e2b8 = 0x20;
      iRam2001e2a0 = 0;
      do {
        ExclusiveAccess(_DAT_2001e270 + 3);
        bVar1 = (bool)hasExclusiveAccess(_DAT_2001e270 + 3);
        if (bVar1) {
          _DAT_2001e270[3] = _DAT_2001e270[3] & 0xffffffef;
          goto LAB_08005216;
        }
        ExclusiveAccess(_DAT_2001e270 + 3);
        bVar1 = (bool)hasExclusiveAccess(_DAT_2001e270 + 3);
        if (bVar1) {
          _DAT_2001e270[3] = _DAT_2001e270[3] & 0xffffffef;
          goto LAB_08005216;
        }
        ExclusiveAccess(_DAT_2001e270 + 3);
        bVar1 = (bool)hasExclusiveAccess(_DAT_2001e270 + 3);
        if (bVar1) {
          _DAT_2001e270[3] = _DAT_2001e270[3] & 0xffffffef;
          goto LAB_08005216;
        }
        ExclusiveAccess(_DAT_2001e270 + 3);
        bVar1 = (bool)hasExclusiveAccess(_DAT_2001e270 + 3);
      } while (!bVar1);
      _DAT_2001e270[3] = _DAT_2001e270[3] & 0xffffffef;
LAB_08005216:
      uRam2001e2a4 = 2;
                    /* WARNING: Could not recover jumptable at 0x08005224. Too many branches */
                    /* WARNING: Treating indirect jump as call */
      (*pcRam2001e2e4)(&DAT_2001e270,sVar5);
      return;
    }
  }
  else if (((int)(uVar6 << 0x18) < 0) && ((uVar8 & 0x80) != 0)) {
    if (iRam2001e2b4 == 0x21) {
      if ((_DAT_2001e278 == 0x1000) && (_DAT_2001e280 == 0)) {
        _DAT_2001e270[1] = *puRam2001e290 & 0x1ff;
        puRam2001e290 = puRam2001e290 + 1;
      }
      else {
        uVar2 = *puRam2001e290;
        puRam2001e290 = (ushort *)((int)puRam2001e290 + 1);
        _DAT_2001e270[1] = (uint)(byte)uVar2;
      }
      sRam2001e296 = sRam2001e296 + -1;
      if (sRam2001e296 == 0) {
        puVar3[3] = puVar3[3] & 0xffffff7f;
        puVar3[3] = puVar3[3] | 0x40;
        return;
      }
    }
  }
  else if (((int)(uVar6 << 0x19) < 0) && ((uVar8 & 0x40) != 0)) {
    _DAT_2001e270[3] = _DAT_2001e270[3] & 0xffffffbf;
    iRam2001e2b4 = 0x20;
                    /* WARNING: Could not recover jumptable at 0x08004dc6. Too many branches */
                    /* WARNING: Treating indirect jump as call */
    (*pcRam2001e2c4)();
    return;
  }
  return;
}



/* 08007774 */

void FUN_08007774(int *param_1)

{
  bool bVar1;
  short sVar2;
  ushort *puVar3;
  int iVar4;
  byte bVar5;
  
  if (param_1[0x12] != 0x22) {
    return;
  }
  if (param_1[2] == 0x1000) {
    puVar3 = (ushort *)param_1[10];
    if (param_1[4] == 0) {
      *puVar3 = (ushort)*(undefined4 *)(*param_1 + 4) & 0x1ff;
      param_1[10] = (int)(puVar3 + 1);
      goto LAB_080077b4;
    }
LAB_08007792:
    bVar5 = (byte)*(undefined4 *)(*param_1 + 4);
  }
  else {
    puVar3 = (ushort *)param_1[10];
    if ((param_1[2] == 0) && (param_1[4] == 0)) goto LAB_08007792;
    bVar5 = (byte)*(undefined4 *)(*param_1 + 4) & 0x7f;
  }
  *(byte *)puVar3 = bVar5;
  param_1[10] = param_1[10] + 1;
LAB_080077b4:
  sVar2 = *(short *)((int)param_1 + 0x2e) + -1;
  *(short *)((int)param_1 + 0x2e) = sVar2;
  if (sVar2 != 0) {
    return;
  }
  iVar4 = *param_1;
  *(uint *)(iVar4 + 0xc) = *(uint *)(iVar4 + 0xc) & 0xffffffdf;
  *(uint *)(iVar4 + 0xc) = *(uint *)(iVar4 + 0xc) & 0xfffffeff;
  *(uint *)(iVar4 + 0x14) = *(uint *)(iVar4 + 0x14) & 0xfffffffe;
  param_1[0x12] = 0x20;
  param_1[0xd] = 0;
  if (param_1[0xc] != 1) {
                    /* WARNING: Could not recover jumptable at 0x0800786c. Too many branches */
                    /* WARNING: Treating indirect jump as call */
    (*(code *)param_1[0x17])();
    return;
  }
  param_1[0xc] = 0;
  do {
    ExclusiveAccess((uint *)(*param_1 + 0xc));
    bVar1 = (bool)hasExclusiveAccess((uint *)(*param_1 + 0xc));
    if (bVar1) {
      *(uint *)(*param_1 + 0xc) = *(uint *)(*param_1 + 0xc) & 0xffffffef;
      goto LAB_08007850;
    }
    ExclusiveAccess((uint *)(*param_1 + 0xc));
    bVar1 = (bool)hasExclusiveAccess((uint *)(*param_1 + 0xc));
    if (bVar1) {
      *(uint *)(*param_1 + 0xc) = *(uint *)(*param_1 + 0xc) & 0xffffffef;
      goto LAB_08007850;
    }
    ExclusiveAccess((uint *)(*param_1 + 0xc));
    bVar1 = (bool)hasExclusiveAccess((uint *)(*param_1 + 0xc));
    if (bVar1) {
      *(uint *)(*param_1 + 0xc) = *(uint *)(*param_1 + 0xc) & 0xffffffef;
      goto LAB_08007850;
    }
    ExclusiveAccess((uint *)(*param_1 + 0xc));
    bVar1 = (bool)hasExclusiveAccess((uint *)(*param_1 + 0xc));
  } while (!bVar1);
  *(uint *)(*param_1 + 0xc) = *(uint *)(*param_1 + 0xc) & 0xffffffef;
LAB_08007850:
                    /* WARNING: Could not recover jumptable at 0x08007856. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*(code *)param_1[0x1d])(param_1,(short)param_1[0xb]);
  return;
}



/* 08007870 */

void FUN_08007870(uint *param_1)

{
  uint uVar1;
  undefined4 uVar2;
  uint uVar3;
  undefined4 uVar4;
  uint uVar5;
  
  uVar1 = *param_1;
  uVar3 = param_1[2];
  uVar5 = param_1[4];
  *(uint *)(uVar1 + 0x10) = param_1[3] | *(uint *)(uVar1 + 0x10) & 0xffffcfff;
  *(uint *)(uVar1 + 0xc) =
       uVar3 | uVar5 | param_1[5] | param_1[7] | *(uint *)(uVar1 + 0xc) & 0xffff69f3;
  *(uint *)(uVar1 + 0x14) = *(uint *)(uVar1 + 0x14) & 0xfffffcff | param_1[6];
  if ((uVar1 | 0x400) == 0x40011400) {
    uVar1 = FUN_08003040();
  }
  else {
    uVar1 = FUN_08003018();
  }
  uVar3 = param_1[1];
  uVar2 = (undefined4)((ulonglong)uVar1 * 0x19);
  uVar4 = (undefined4)((ulonglong)uVar1 * 0x19 >> 0x20);
  if (param_1[7] == 0x8000) {
    uVar1 = FUN_08000326(uVar2,uVar4,uVar3 << 1,uVar3 >> 0x1f);
    uVar3 = ((uVar1 / 100) * 0x1fffff9c + uVar1) * 8 + 0x32;
    *(uint *)(*param_1 + 8) =
         (uVar3 / 0x32 & 0x1f0) + (uVar1 / 100) * 0x10 +
         (((uint)((ulonglong)uVar3 * 0x51eb851f >> 0x20) & 0xff) >> 5);
    return;
  }
  uVar1 = FUN_08000326(uVar2,uVar4,uVar3 << 2,uVar3 >> 0x1e);
  uVar3 = ((uVar1 / 100) * 0xfffff9c + uVar1) * 0x10 + 0x32;
  *(uint *)(*param_1 + 8) =
       (uVar3 / 100 & 0xf0) + (uVar1 / 100) * 0x10 +
       (((uint)((ulonglong)uVar3 * 0x51eb851f >> 0x20) & 0x1ff) >> 5);
  return;
}



/* 08007958 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void IRQ_38_Handler(void)

{
  bool bVar1;
  ushort uVar2;
  uint *puVar3;
  int *piVar4;
  short sVar5;
  uint uVar6;
  uint uVar7;
  uint uVar8;
  uint uVar9;
  int iVar10;
  uint unaff_lr;
  
  puVar3 = _DAT_2001e170;
  uVar6 = *_DAT_2001e170;
  uVar8 = _DAT_2001e170[3];
  uVar7 = _DAT_2001e170[5];
  uVar9 = uVar8 & 0x20;
  if (((uVar6 & 0x2f) == 0x20) && (uVar9 != 0)) {
    FUN_08007774();
    return;
  }
  iVar10 = uVar6 * 0x10000000;
  if (iVar10 != 0) {
    unaff_lr = uVar7 & 1;
    uVar7 = uVar8 & 0x120;
  }
  if (iVar10 != 0 && uVar7 + unaff_lr != 0) {
    if ((uVar6 & 1) != 0 && (uVar8 & 0x100) != 0) {
      _DAT_2001e1bc = _DAT_2001e1bc | 1;
    }
    if (((int)(uVar6 << 0x1d) < 0) && (unaff_lr != 0)) {
      _DAT_2001e1bc = _DAT_2001e1bc | 2;
    }
    if (((int)(uVar6 << 0x1e) < 0) && (unaff_lr != 0)) {
      _DAT_2001e1bc = _DAT_2001e1bc | 4;
    }
    if ((iVar10 < 0) && (unaff_lr != 0 || uVar9 != 0)) {
      _DAT_2001e1bc = _DAT_2001e1bc | 8;
    }
    if (_DAT_2001e1bc != 0) {
      if (((int)(uVar6 << 0x1a) < 0) && (uVar9 != 0)) {
        FUN_08007774();
      }
      if ((_DAT_2001e170[5] & 0x40) + (_DAT_2001e1bc & 8) == 0) {
        (*_DAT_2001e1d0)();
        _DAT_2001e1bc = 0;
        return;
      }
      do {
        ExclusiveAccess(_DAT_2001e170 + 3);
        bVar1 = (bool)hasExclusiveAccess(_DAT_2001e170 + 3);
        if (bVar1) {
          _DAT_2001e170[3] = _DAT_2001e170[3] & 0xfffffedf;
          goto LAB_0800502a;
        }
        ExclusiveAccess(_DAT_2001e170 + 3);
        bVar1 = (bool)hasExclusiveAccess(_DAT_2001e170 + 3);
        if (bVar1) {
          _DAT_2001e170[3] = _DAT_2001e170[3] & 0xfffffedf;
          goto LAB_0800502a;
        }
        ExclusiveAccess(_DAT_2001e170 + 3);
        bVar1 = (bool)hasExclusiveAccess(_DAT_2001e170 + 3);
        if (bVar1) {
          _DAT_2001e170[3] = _DAT_2001e170[3] & 0xfffffedf;
          goto LAB_0800502a;
        }
        ExclusiveAccess(_DAT_2001e170 + 3);
        bVar1 = (bool)hasExclusiveAccess(_DAT_2001e170 + 3);
      } while (!bVar1);
      _DAT_2001e170[3] = _DAT_2001e170[3] & 0xfffffedf;
LAB_0800502a:
      do {
        ExclusiveAccess(_DAT_2001e170 + 5);
        bVar1 = (bool)hasExclusiveAccess(_DAT_2001e170 + 5);
        if (bVar1) {
          _DAT_2001e170[5] = _DAT_2001e170[5] & 0xfffffffe;
          goto LAB_0800503e;
        }
        ExclusiveAccess(_DAT_2001e170 + 5);
        bVar1 = (bool)hasExclusiveAccess(_DAT_2001e170 + 5);
        if (bVar1) {
          _DAT_2001e170[5] = _DAT_2001e170[5] & 0xfffffffe;
          goto LAB_0800503e;
        }
        ExclusiveAccess(_DAT_2001e170 + 5);
        bVar1 = (bool)hasExclusiveAccess(_DAT_2001e170 + 5);
        if (bVar1) {
          _DAT_2001e170[5] = _DAT_2001e170[5] & 0xfffffffe;
          goto LAB_0800503e;
        }
        ExclusiveAccess(_DAT_2001e170 + 5);
        bVar1 = (bool)hasExclusiveAccess(_DAT_2001e170 + 5);
      } while (!bVar1);
      _DAT_2001e170[5] = _DAT_2001e170[5] & 0xfffffffe;
LAB_0800503e:
      if (_DAT_2001e1a0 == 1) {
        do {
          ExclusiveAccess(_DAT_2001e170 + 3);
          bVar1 = (bool)hasExclusiveAccess(_DAT_2001e170 + 3);
          if (bVar1) {
            _DAT_2001e170[3] = _DAT_2001e170[3] & 0xffffffef;
            goto LAB_0800508e;
          }
          ExclusiveAccess(_DAT_2001e170 + 3);
          bVar1 = (bool)hasExclusiveAccess(_DAT_2001e170 + 3);
          if (bVar1) {
            _DAT_2001e170[3] = _DAT_2001e170[3] & 0xffffffef;
            goto LAB_0800508e;
          }
          ExclusiveAccess(_DAT_2001e170 + 3);
          bVar1 = (bool)hasExclusiveAccess(_DAT_2001e170 + 3);
          if (bVar1) {
            _DAT_2001e170[3] = _DAT_2001e170[3] & 0xffffffef;
            goto LAB_0800508e;
          }
          ExclusiveAccess(_DAT_2001e170 + 3);
          bVar1 = (bool)hasExclusiveAccess(_DAT_2001e170 + 3);
        } while (!bVar1);
        _DAT_2001e170[3] = _DAT_2001e170[3] & 0xffffffef;
      }
LAB_0800508e:
      _DAT_2001e1b8 = 0x20;
      _DAT_2001e1a0 = 0;
      if ((int)(_DAT_2001e170[5] << 0x19) < 0) {
        do {
          ExclusiveAccess(_DAT_2001e170 + 5);
          bVar1 = (bool)hasExclusiveAccess(_DAT_2001e170 + 5);
          if (bVar1) {
            _DAT_2001e170[5] = _DAT_2001e170[5] & 0xffffffbf;
            goto LAB_080050ea;
          }
          ExclusiveAccess(_DAT_2001e170 + 5);
          bVar1 = (bool)hasExclusiveAccess(_DAT_2001e170 + 5);
          if (bVar1) {
            _DAT_2001e170[5] = _DAT_2001e170[5] & 0xffffffbf;
            goto LAB_080050ea;
          }
          ExclusiveAccess(_DAT_2001e170 + 5);
          bVar1 = (bool)hasExclusiveAccess(_DAT_2001e170 + 5);
          if (bVar1) {
            _DAT_2001e170[5] = _DAT_2001e170[5] & 0xffffffbf;
            goto LAB_080050ea;
          }
          ExclusiveAccess(_DAT_2001e170 + 5);
          bVar1 = (bool)hasExclusiveAccess(_DAT_2001e170 + 5);
        } while (!bVar1);
        _DAT_2001e170[5] = _DAT_2001e170[5] & 0xffffffbf;
LAB_080050ea:
        piVar4 = _DAT_2001e1ac;
        if (_DAT_2001e1ac != (int *)0x0) {
          _DAT_2001e1ac[0x15] = (int)&LAB_080073c4_1;
          iVar10 = FUN_080019e8(piVar4);
          if (iVar10 == 0) {
            return;
          }
                    /* WARNING: Could not recover jumptable at 0x08005114. Too many branches */
                    /* WARNING: Treating indirect jump as call */
          (*(code *)_DAT_2001e1ac[0x15])();
          return;
        }
      }
                    /* WARNING: Could not recover jumptable at 0x08005230. Too many branches */
                    /* WARNING: Treating indirect jump as call */
      (*_DAT_2001e1d0)();
      return;
    }
  }
  else if ((((int)(uVar6 << 0x1b) < 0) && (_DAT_2001e1a0 == 1)) && ((uVar8 & 0x10) != 0)) {
    if ((int)(_DAT_2001e170[5] << 0x19) < 0) {
      sVar5 = (short)*(uint *)(*_DAT_2001e1ac + 4);
      uVar7 = *(uint *)(*_DAT_2001e1ac + 4) & 0xffff;
      if ((uVar7 != 0) && (uVar7 < _DAT_2001e19c)) {
        _DAT_2001e19e = sVar5;
        if (_DAT_2001e1ac[7] != 0x100) {
          do {
            ExclusiveAccess(_DAT_2001e170 + 3);
            bVar1 = (bool)hasExclusiveAccess(_DAT_2001e170 + 3);
            if (bVar1) {
              _DAT_2001e170[3] = _DAT_2001e170[3] & 0xfffffeff;
              goto LAB_08004e30;
            }
            ExclusiveAccess(_DAT_2001e170 + 3);
            bVar1 = (bool)hasExclusiveAccess(_DAT_2001e170 + 3);
            if (bVar1) {
              _DAT_2001e170[3] = _DAT_2001e170[3] & 0xfffffeff;
              goto LAB_08004e30;
            }
            ExclusiveAccess(_DAT_2001e170 + 3);
            bVar1 = (bool)hasExclusiveAccess(_DAT_2001e170 + 3);
            if (bVar1) {
              _DAT_2001e170[3] = _DAT_2001e170[3] & 0xfffffeff;
              goto LAB_08004e30;
            }
            ExclusiveAccess(_DAT_2001e170 + 3);
            bVar1 = (bool)hasExclusiveAccess(_DAT_2001e170 + 3);
          } while (!bVar1);
          _DAT_2001e170[3] = _DAT_2001e170[3] & 0xfffffeff;
LAB_08004e30:
          do {
            ExclusiveAccess(_DAT_2001e170 + 5);
            bVar1 = (bool)hasExclusiveAccess(_DAT_2001e170 + 5);
            if (bVar1) {
              _DAT_2001e170[5] = _DAT_2001e170[5] & 0xfffffffe;
              goto LAB_08004eb2;
            }
            ExclusiveAccess(_DAT_2001e170 + 5);
            bVar1 = (bool)hasExclusiveAccess(_DAT_2001e170 + 5);
            if (bVar1) {
              _DAT_2001e170[5] = _DAT_2001e170[5] & 0xfffffffe;
              goto LAB_08004eb2;
            }
            ExclusiveAccess(_DAT_2001e170 + 5);
            bVar1 = (bool)hasExclusiveAccess(_DAT_2001e170 + 5);
            if (bVar1) {
              _DAT_2001e170[5] = _DAT_2001e170[5] & 0xfffffffe;
              goto LAB_08004eb2;
            }
            ExclusiveAccess(_DAT_2001e170 + 5);
            bVar1 = (bool)hasExclusiveAccess(_DAT_2001e170 + 5);
          } while (!bVar1);
          _DAT_2001e170[5] = _DAT_2001e170[5] & 0xfffffffe;
LAB_08004eb2:
          do {
            ExclusiveAccess(_DAT_2001e170 + 5);
            bVar1 = (bool)hasExclusiveAccess(_DAT_2001e170 + 5);
            if (bVar1) {
              _DAT_2001e170[5] = _DAT_2001e170[5] & 0xffffffbf;
              goto LAB_08004ec6;
            }
            ExclusiveAccess(_DAT_2001e170 + 5);
            bVar1 = (bool)hasExclusiveAccess(_DAT_2001e170 + 5);
            if (bVar1) {
              _DAT_2001e170[5] = _DAT_2001e170[5] & 0xffffffbf;
              goto LAB_08004ec6;
            }
            ExclusiveAccess(_DAT_2001e170 + 5);
            bVar1 = (bool)hasExclusiveAccess(_DAT_2001e170 + 5);
            if (bVar1) {
              _DAT_2001e170[5] = _DAT_2001e170[5] & 0xffffffbf;
              goto LAB_08004ec6;
            }
            ExclusiveAccess(_DAT_2001e170 + 5);
            bVar1 = (bool)hasExclusiveAccess(_DAT_2001e170 + 5);
          } while (!bVar1);
          _DAT_2001e170[5] = _DAT_2001e170[5] & 0xffffffbf;
LAB_08004ec6:
          _DAT_2001e1b8 = 0x20;
          _DAT_2001e1a0 = 0;
          do {
            ExclusiveAccess(_DAT_2001e170 + 3);
            bVar1 = (bool)hasExclusiveAccess(_DAT_2001e170 + 3);
            if (bVar1) {
              _DAT_2001e170[3] = _DAT_2001e170[3] & 0xffffffef;
              goto LAB_08004f18;
            }
            ExclusiveAccess(_DAT_2001e170 + 3);
            bVar1 = (bool)hasExclusiveAccess(_DAT_2001e170 + 3);
            if (bVar1) {
              _DAT_2001e170[3] = _DAT_2001e170[3] & 0xffffffef;
              goto LAB_08004f18;
            }
            ExclusiveAccess(_DAT_2001e170 + 3);
            bVar1 = (bool)hasExclusiveAccess(_DAT_2001e170 + 3);
            if (bVar1) {
              _DAT_2001e170[3] = _DAT_2001e170[3] & 0xffffffef;
              goto LAB_08004f18;
            }
            ExclusiveAccess(_DAT_2001e170 + 3);
            bVar1 = (bool)hasExclusiveAccess(_DAT_2001e170 + 3);
          } while (!bVar1);
          _DAT_2001e170[3] = _DAT_2001e170[3] & 0xffffffef;
LAB_08004f18:
          FUN_08001968(_DAT_2001e1ac);
        }
        _DAT_2001e1a4 = 2;
                    /* WARNING: Could not recover jumptable at 0x08004f38. Too many branches */
                    /* WARNING: Treating indirect jump as call */
        (*_DAT_2001e1e4)(&DAT_2001e170,_DAT_2001e19c - _DAT_2001e19e);
        return;
      }
    }
    else if (_DAT_2001e19e != 0 && _DAT_2001e19c != _DAT_2001e19e) {
      sVar5 = _DAT_2001e19c - _DAT_2001e19e;
      do {
        ExclusiveAccess(_DAT_2001e170 + 3);
        bVar1 = (bool)hasExclusiveAccess(_DAT_2001e170 + 3);
        if (bVar1) {
          _DAT_2001e170[3] = _DAT_2001e170[3] & 0xfffffedf;
          goto LAB_080051ae;
        }
        ExclusiveAccess(_DAT_2001e170 + 3);
        bVar1 = (bool)hasExclusiveAccess(_DAT_2001e170 + 3);
        if (bVar1) {
          _DAT_2001e170[3] = _DAT_2001e170[3] & 0xfffffedf;
          goto LAB_080051ae;
        }
        ExclusiveAccess(_DAT_2001e170 + 3);
        bVar1 = (bool)hasExclusiveAccess(_DAT_2001e170 + 3);
        if (bVar1) {
          _DAT_2001e170[3] = _DAT_2001e170[3] & 0xfffffedf;
          goto LAB_080051ae;
        }
        ExclusiveAccess(_DAT_2001e170 + 3);
        bVar1 = (bool)hasExclusiveAccess(_DAT_2001e170 + 3);
      } while (!bVar1);
      _DAT_2001e170[3] = _DAT_2001e170[3] & 0xfffffedf;
LAB_080051ae:
      do {
        ExclusiveAccess(_DAT_2001e170 + 5);
        bVar1 = (bool)hasExclusiveAccess(_DAT_2001e170 + 5);
        if (bVar1) {
          _DAT_2001e170[5] = _DAT_2001e170[5] & 0xfffffffe;
          goto LAB_080051c2;
        }
        ExclusiveAccess(_DAT_2001e170 + 5);
        bVar1 = (bool)hasExclusiveAccess(_DAT_2001e170 + 5);
        if (bVar1) {
          _DAT_2001e170[5] = _DAT_2001e170[5] & 0xfffffffe;
          goto LAB_080051c2;
        }
        ExclusiveAccess(_DAT_2001e170 + 5);
        bVar1 = (bool)hasExclusiveAccess(_DAT_2001e170 + 5);
        if (bVar1) {
          _DAT_2001e170[5] = _DAT_2001e170[5] & 0xfffffffe;
          goto LAB_080051c2;
        }
        ExclusiveAccess(_DAT_2001e170 + 5);
        bVar1 = (bool)hasExclusiveAccess(_DAT_2001e170 + 5);
      } while (!bVar1);
      _DAT_2001e170[5] = _DAT_2001e170[5] & 0xfffffffe;
LAB_080051c2:
      _DAT_2001e1b8 = 0x20;
      _DAT_2001e1a0 = 0;
      do {
        ExclusiveAccess(_DAT_2001e170 + 3);
        bVar1 = (bool)hasExclusiveAccess(_DAT_2001e170 + 3);
        if (bVar1) {
          _DAT_2001e170[3] = _DAT_2001e170[3] & 0xffffffef;
          goto LAB_08005216;
        }
        ExclusiveAccess(_DAT_2001e170 + 3);
        bVar1 = (bool)hasExclusiveAccess(_DAT_2001e170 + 3);
        if (bVar1) {
          _DAT_2001e170[3] = _DAT_2001e170[3] & 0xffffffef;
          goto LAB_08005216;
        }
        ExclusiveAccess(_DAT_2001e170 + 3);
        bVar1 = (bool)hasExclusiveAccess(_DAT_2001e170 + 3);
        if (bVar1) {
          _DAT_2001e170[3] = _DAT_2001e170[3] & 0xffffffef;
          goto LAB_08005216;
        }
        ExclusiveAccess(_DAT_2001e170 + 3);
        bVar1 = (bool)hasExclusiveAccess(_DAT_2001e170 + 3);
      } while (!bVar1);
      _DAT_2001e170[3] = _DAT_2001e170[3] & 0xffffffef;
LAB_08005216:
      _DAT_2001e1a4 = 2;
                    /* WARNING: Could not recover jumptable at 0x08005224. Too many branches */
                    /* WARNING: Treating indirect jump as call */
      (*_DAT_2001e1e4)(&DAT_2001e170,sVar5);
      return;
    }
  }
  else if (((int)(uVar6 << 0x18) < 0) && ((uVar8 & 0x80) != 0)) {
    if (_DAT_2001e1b4 == 0x21) {
      if ((_DAT_2001e178 == 0x1000) && (_DAT_2001e180 == 0)) {
        _DAT_2001e170[1] = *_DAT_2001e190 & 0x1ff;
        _DAT_2001e190 = _DAT_2001e190 + 1;
      }
      else {
        uVar2 = *_DAT_2001e190;
        _DAT_2001e190 = (ushort *)((int)_DAT_2001e190 + 1);
        _DAT_2001e170[1] = (uint)(byte)uVar2;
      }
      _DAT_2001e196 = _DAT_2001e196 + -1;
      if (_DAT_2001e196 == 0) {
        puVar3[3] = puVar3[3] & 0xffffff7f;
        puVar3[3] = puVar3[3] | 0x40;
        return;
      }
    }
  }
  else if (((int)(uVar6 << 0x19) < 0) && ((uVar8 & 0x40) != 0)) {
    _DAT_2001e170[3] = _DAT_2001e170[3] & 0xffffffbf;
    _DAT_2001e1b4 = 0x20;
                    /* WARNING: Could not recover jumptable at 0x08004dc6. Too many branches */
                    /* WARNING: Treating indirect jump as call */
    (*_DAT_2001e1c4)();
    return;
  }
  return;
}



/* 08007964 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void IRQ_39_Handler(void)

{
  bool bVar1;
  ushort uVar2;
  uint *puVar3;
  int *piVar4;
  short sVar5;
  uint uVar6;
  uint uVar7;
  uint uVar8;
  uint uVar9;
  int iVar10;
  uint unaff_lr;
  
  puVar3 = _DAT_2001e1f0;
  _DAT_2001e230 = 0;
  uVar6 = *_DAT_2001e1f0;
  uVar8 = _DAT_2001e1f0[3];
  uVar7 = _DAT_2001e1f0[5];
  uVar9 = uVar8 & 0x20;
  if (((uVar6 & 0x2f) == 0x20) && (uVar9 != 0)) {
    FUN_08007774();
    return;
  }
  iVar10 = uVar6 * 0x10000000;
  if (iVar10 != 0) {
    unaff_lr = uVar7 & 1;
    uVar7 = uVar8 & 0x120;
  }
  if (iVar10 != 0 && uVar7 + unaff_lr != 0) {
    if ((uVar6 & 1) != 0 && (uVar8 & 0x100) != 0) {
      uRam2001e23c = uRam2001e23c | 1;
    }
    if (((int)(uVar6 << 0x1d) < 0) && (unaff_lr != 0)) {
      uRam2001e23c = uRam2001e23c | 2;
    }
    if (((int)(uVar6 << 0x1e) < 0) && (unaff_lr != 0)) {
      uRam2001e23c = uRam2001e23c | 4;
    }
    if ((iVar10 < 0) && (unaff_lr != 0 || uVar9 != 0)) {
      uRam2001e23c = uRam2001e23c | 8;
    }
    if (uRam2001e23c != 0) {
      if (((int)(uVar6 << 0x1a) < 0) && (uVar9 != 0)) {
        FUN_08007774();
      }
      if ((_DAT_2001e1f0[5] & 0x40) + (uRam2001e23c & 8) == 0) {
        (*pcRam2001e250)();
        uRam2001e23c = 0;
        return;
      }
      do {
        ExclusiveAccess(_DAT_2001e1f0 + 3);
        bVar1 = (bool)hasExclusiveAccess(_DAT_2001e1f0 + 3);
        if (bVar1) {
          _DAT_2001e1f0[3] = _DAT_2001e1f0[3] & 0xfffffedf;
          goto LAB_0800502a;
        }
        ExclusiveAccess(_DAT_2001e1f0 + 3);
        bVar1 = (bool)hasExclusiveAccess(_DAT_2001e1f0 + 3);
        if (bVar1) {
          _DAT_2001e1f0[3] = _DAT_2001e1f0[3] & 0xfffffedf;
          goto LAB_0800502a;
        }
        ExclusiveAccess(_DAT_2001e1f0 + 3);
        bVar1 = (bool)hasExclusiveAccess(_DAT_2001e1f0 + 3);
        if (bVar1) {
          _DAT_2001e1f0[3] = _DAT_2001e1f0[3] & 0xfffffedf;
          goto LAB_0800502a;
        }
        ExclusiveAccess(_DAT_2001e1f0 + 3);
        bVar1 = (bool)hasExclusiveAccess(_DAT_2001e1f0 + 3);
      } while (!bVar1);
      _DAT_2001e1f0[3] = _DAT_2001e1f0[3] & 0xfffffedf;
LAB_0800502a:
      do {
        ExclusiveAccess(_DAT_2001e1f0 + 5);
        bVar1 = (bool)hasExclusiveAccess(_DAT_2001e1f0 + 5);
        if (bVar1) {
          _DAT_2001e1f0[5] = _DAT_2001e1f0[5] & 0xfffffffe;
          goto LAB_0800503e;
        }
        ExclusiveAccess(_DAT_2001e1f0 + 5);
        bVar1 = (bool)hasExclusiveAccess(_DAT_2001e1f0 + 5);
        if (bVar1) {
          _DAT_2001e1f0[5] = _DAT_2001e1f0[5] & 0xfffffffe;
          goto LAB_0800503e;
        }
        ExclusiveAccess(_DAT_2001e1f0 + 5);
        bVar1 = (bool)hasExclusiveAccess(_DAT_2001e1f0 + 5);
        if (bVar1) {
          _DAT_2001e1f0[5] = _DAT_2001e1f0[5] & 0xfffffffe;
          goto LAB_0800503e;
        }
        ExclusiveAccess(_DAT_2001e1f0 + 5);
        bVar1 = (bool)hasExclusiveAccess(_DAT_2001e1f0 + 5);
      } while (!bVar1);
      _DAT_2001e1f0[5] = _DAT_2001e1f0[5] & 0xfffffffe;
LAB_0800503e:
      if (iRam2001e220 == 1) {
        do {
          ExclusiveAccess(_DAT_2001e1f0 + 3);
          bVar1 = (bool)hasExclusiveAccess(_DAT_2001e1f0 + 3);
          if (bVar1) {
            _DAT_2001e1f0[3] = _DAT_2001e1f0[3] & 0xffffffef;
            goto LAB_0800508e;
          }
          ExclusiveAccess(_DAT_2001e1f0 + 3);
          bVar1 = (bool)hasExclusiveAccess(_DAT_2001e1f0 + 3);
          if (bVar1) {
            _DAT_2001e1f0[3] = _DAT_2001e1f0[3] & 0xffffffef;
            goto LAB_0800508e;
          }
          ExclusiveAccess(_DAT_2001e1f0 + 3);
          bVar1 = (bool)hasExclusiveAccess(_DAT_2001e1f0 + 3);
          if (bVar1) {
            _DAT_2001e1f0[3] = _DAT_2001e1f0[3] & 0xffffffef;
            goto LAB_0800508e;
          }
          ExclusiveAccess(_DAT_2001e1f0 + 3);
          bVar1 = (bool)hasExclusiveAccess(_DAT_2001e1f0 + 3);
        } while (!bVar1);
        _DAT_2001e1f0[3] = _DAT_2001e1f0[3] & 0xffffffef;
      }
LAB_0800508e:
      uRam2001e238 = 0x20;
      iRam2001e220 = 0;
      if ((int)(_DAT_2001e1f0[5] << 0x19) < 0) {
        do {
          ExclusiveAccess(_DAT_2001e1f0 + 5);
          bVar1 = (bool)hasExclusiveAccess(_DAT_2001e1f0 + 5);
          if (bVar1) {
            _DAT_2001e1f0[5] = _DAT_2001e1f0[5] & 0xffffffbf;
            goto LAB_080050ea;
          }
          ExclusiveAccess(_DAT_2001e1f0 + 5);
          bVar1 = (bool)hasExclusiveAccess(_DAT_2001e1f0 + 5);
          if (bVar1) {
            _DAT_2001e1f0[5] = _DAT_2001e1f0[5] & 0xffffffbf;
            goto LAB_080050ea;
          }
          ExclusiveAccess(_DAT_2001e1f0 + 5);
          bVar1 = (bool)hasExclusiveAccess(_DAT_2001e1f0 + 5);
          if (bVar1) {
            _DAT_2001e1f0[5] = _DAT_2001e1f0[5] & 0xffffffbf;
            goto LAB_080050ea;
          }
          ExclusiveAccess(_DAT_2001e1f0 + 5);
          bVar1 = (bool)hasExclusiveAccess(_DAT_2001e1f0 + 5);
        } while (!bVar1);
        _DAT_2001e1f0[5] = _DAT_2001e1f0[5] & 0xffffffbf;
LAB_080050ea:
        piVar4 = piRam2001e22c;
        if (piRam2001e22c != (int *)0x0) {
          piRam2001e22c[0x15] = (int)&LAB_080073c4_1;
          iVar10 = FUN_080019e8(piVar4);
          if (iVar10 == 0) {
            return;
          }
                    /* WARNING: Could not recover jumptable at 0x08005114. Too many branches */
                    /* WARNING: Treating indirect jump as call */
          (*(code *)piRam2001e22c[0x15])();
          return;
        }
      }
                    /* WARNING: Could not recover jumptable at 0x08005230. Too many branches */
                    /* WARNING: Treating indirect jump as call */
      (*pcRam2001e250)();
      return;
    }
  }
  else if ((((int)(uVar6 << 0x1b) < 0) && (iRam2001e220 == 1)) && ((uVar8 & 0x10) != 0)) {
    if ((int)(_DAT_2001e1f0[5] << 0x19) < 0) {
      sVar5 = (short)*(uint *)(*piRam2001e22c + 4);
      uVar7 = *(uint *)(*piRam2001e22c + 4) & 0xffff;
      if ((uVar7 != 0) && (uVar7 < uRam2001e21c)) {
        uRam2001e21e = sVar5;
        if (piRam2001e22c[7] != 0x100) {
          do {
            ExclusiveAccess(_DAT_2001e1f0 + 3);
            bVar1 = (bool)hasExclusiveAccess(_DAT_2001e1f0 + 3);
            if (bVar1) {
              _DAT_2001e1f0[3] = _DAT_2001e1f0[3] & 0xfffffeff;
              goto LAB_08004e30;
            }
            ExclusiveAccess(_DAT_2001e1f0 + 3);
            bVar1 = (bool)hasExclusiveAccess(_DAT_2001e1f0 + 3);
            if (bVar1) {
              _DAT_2001e1f0[3] = _DAT_2001e1f0[3] & 0xfffffeff;
              goto LAB_08004e30;
            }
            ExclusiveAccess(_DAT_2001e1f0 + 3);
            bVar1 = (bool)hasExclusiveAccess(_DAT_2001e1f0 + 3);
            if (bVar1) {
              _DAT_2001e1f0[3] = _DAT_2001e1f0[3] & 0xfffffeff;
              goto LAB_08004e30;
            }
            ExclusiveAccess(_DAT_2001e1f0 + 3);
            bVar1 = (bool)hasExclusiveAccess(_DAT_2001e1f0 + 3);
          } while (!bVar1);
          _DAT_2001e1f0[3] = _DAT_2001e1f0[3] & 0xfffffeff;
LAB_08004e30:
          do {
            ExclusiveAccess(_DAT_2001e1f0 + 5);
            bVar1 = (bool)hasExclusiveAccess(_DAT_2001e1f0 + 5);
            if (bVar1) {
              _DAT_2001e1f0[5] = _DAT_2001e1f0[5] & 0xfffffffe;
              goto LAB_08004eb2;
            }
            ExclusiveAccess(_DAT_2001e1f0 + 5);
            bVar1 = (bool)hasExclusiveAccess(_DAT_2001e1f0 + 5);
            if (bVar1) {
              _DAT_2001e1f0[5] = _DAT_2001e1f0[5] & 0xfffffffe;
              goto LAB_08004eb2;
            }
            ExclusiveAccess(_DAT_2001e1f0 + 5);
            bVar1 = (bool)hasExclusiveAccess(_DAT_2001e1f0 + 5);
            if (bVar1) {
              _DAT_2001e1f0[5] = _DAT_2001e1f0[5] & 0xfffffffe;
              goto LAB_08004eb2;
            }
            ExclusiveAccess(_DAT_2001e1f0 + 5);
            bVar1 = (bool)hasExclusiveAccess(_DAT_2001e1f0 + 5);
          } while (!bVar1);
          _DAT_2001e1f0[5] = _DAT_2001e1f0[5] & 0xfffffffe;
LAB_08004eb2:
          do {
            ExclusiveAccess(_DAT_2001e1f0 + 5);
            bVar1 = (bool)hasExclusiveAccess(_DAT_2001e1f0 + 5);
            if (bVar1) {
              _DAT_2001e1f0[5] = _DAT_2001e1f0[5] & 0xffffffbf;
              goto LAB_08004ec6;
            }
            ExclusiveAccess(_DAT_2001e1f0 + 5);
            bVar1 = (bool)hasExclusiveAccess(_DAT_2001e1f0 + 5);
            if (bVar1) {
              _DAT_2001e1f0[5] = _DAT_2001e1f0[5] & 0xffffffbf;
              goto LAB_08004ec6;
            }
            ExclusiveAccess(_DAT_2001e1f0 + 5);
            bVar1 = (bool)hasExclusiveAccess(_DAT_2001e1f0 + 5);
            if (bVar1) {
              _DAT_2001e1f0[5] = _DAT_2001e1f0[5] & 0xffffffbf;
              goto LAB_08004ec6;
            }
            ExclusiveAccess(_DAT_2001e1f0 + 5);
            bVar1 = (bool)hasExclusiveAccess(_DAT_2001e1f0 + 5);
          } while (!bVar1);
          _DAT_2001e1f0[5] = _DAT_2001e1f0[5] & 0xffffffbf;
LAB_08004ec6:
          uRam2001e238 = 0x20;
          iRam2001e220 = 0;
          do {
            ExclusiveAccess(_DAT_2001e1f0 + 3);
            bVar1 = (bool)hasExclusiveAccess(_DAT_2001e1f0 + 3);
            if (bVar1) {
              _DAT_2001e1f0[3] = _DAT_2001e1f0[3] & 0xffffffef;
              goto LAB_08004f18;
            }
            ExclusiveAccess(_DAT_2001e1f0 + 3);
            bVar1 = (bool)hasExclusiveAccess(_DAT_2001e1f0 + 3);
            if (bVar1) {
              _DAT_2001e1f0[3] = _DAT_2001e1f0[3] & 0xffffffef;
              goto LAB_08004f18;
            }
            ExclusiveAccess(_DAT_2001e1f0 + 3);
            bVar1 = (bool)hasExclusiveAccess(_DAT_2001e1f0 + 3);
            if (bVar1) {
              _DAT_2001e1f0[3] = _DAT_2001e1f0[3] & 0xffffffef;
              goto LAB_08004f18;
            }
            ExclusiveAccess(_DAT_2001e1f0 + 3);
            bVar1 = (bool)hasExclusiveAccess(_DAT_2001e1f0 + 3);
          } while (!bVar1);
          _DAT_2001e1f0[3] = _DAT_2001e1f0[3] & 0xffffffef;
LAB_08004f18:
          FUN_08001968(piRam2001e22c);
        }
        uRam2001e224 = 2;
                    /* WARNING: Could not recover jumptable at 0x08004f38. Too many branches */
                    /* WARNING: Treating indirect jump as call */
        (*pcRam2001e264)(&DAT_2001e1f0,uRam2001e21c - uRam2001e21e);
        return;
      }
    }
    else if (uRam2001e21e != 0 && uRam2001e21c != uRam2001e21e) {
      sVar5 = uRam2001e21c - uRam2001e21e;
      do {
        ExclusiveAccess(_DAT_2001e1f0 + 3);
        bVar1 = (bool)hasExclusiveAccess(_DAT_2001e1f0 + 3);
        if (bVar1) {
          _DAT_2001e1f0[3] = _DAT_2001e1f0[3] & 0xfffffedf;
          goto LAB_080051ae;
        }
        ExclusiveAccess(_DAT_2001e1f0 + 3);
        bVar1 = (bool)hasExclusiveAccess(_DAT_2001e1f0 + 3);
        if (bVar1) {
          _DAT_2001e1f0[3] = _DAT_2001e1f0[3] & 0xfffffedf;
          goto LAB_080051ae;
        }
        ExclusiveAccess(_DAT_2001e1f0 + 3);
        bVar1 = (bool)hasExclusiveAccess(_DAT_2001e1f0 + 3);
        if (bVar1) {
          _DAT_2001e1f0[3] = _DAT_2001e1f0[3] & 0xfffffedf;
          goto LAB_080051ae;
        }
        ExclusiveAccess(_DAT_2001e1f0 + 3);
        bVar1 = (bool)hasExclusiveAccess(_DAT_2001e1f0 + 3);
      } while (!bVar1);
      _DAT_2001e1f0[3] = _DAT_2001e1f0[3] & 0xfffffedf;
LAB_080051ae:
      do {
        ExclusiveAccess(_DAT_2001e1f0 + 5);
        bVar1 = (bool)hasExclusiveAccess(_DAT_2001e1f0 + 5);
        if (bVar1) {
          _DAT_2001e1f0[5] = _DAT_2001e1f0[5] & 0xfffffffe;
          goto LAB_080051c2;
        }
        ExclusiveAccess(_DAT_2001e1f0 + 5);
        bVar1 = (bool)hasExclusiveAccess(_DAT_2001e1f0 + 5);
        if (bVar1) {
          _DAT_2001e1f0[5] = _DAT_2001e1f0[5] & 0xfffffffe;
          goto LAB_080051c2;
        }
        ExclusiveAccess(_DAT_2001e1f0 + 5);
        bVar1 = (bool)hasExclusiveAccess(_DAT_2001e1f0 + 5);
        if (bVar1) {
          _DAT_2001e1f0[5] = _DAT_2001e1f0[5] & 0xfffffffe;
          goto LAB_080051c2;
        }
        ExclusiveAccess(_DAT_2001e1f0 + 5);
        bVar1 = (bool)hasExclusiveAccess(_DAT_2001e1f0 + 5);
      } while (!bVar1);
      _DAT_2001e1f0[5] = _DAT_2001e1f0[5] & 0xfffffffe;
LAB_080051c2:
      uRam2001e238 = 0x20;
      iRam2001e220 = 0;
      do {
        ExclusiveAccess(_DAT_2001e1f0 + 3);
        bVar1 = (bool)hasExclusiveAccess(_DAT_2001e1f0 + 3);
        if (bVar1) {
          _DAT_2001e1f0[3] = _DAT_2001e1f0[3] & 0xffffffef;
          goto LAB_08005216;
        }
        ExclusiveAccess(_DAT_2001e1f0 + 3);
        bVar1 = (bool)hasExclusiveAccess(_DAT_2001e1f0 + 3);
        if (bVar1) {
          _DAT_2001e1f0[3] = _DAT_2001e1f0[3] & 0xffffffef;
          goto LAB_08005216;
        }
        ExclusiveAccess(_DAT_2001e1f0 + 3);
        bVar1 = (bool)hasExclusiveAccess(_DAT_2001e1f0 + 3);
        if (bVar1) {
          _DAT_2001e1f0[3] = _DAT_2001e1f0[3] & 0xffffffef;
          goto LAB_08005216;
        }
        ExclusiveAccess(_DAT_2001e1f0 + 3);
        bVar1 = (bool)hasExclusiveAccess(_DAT_2001e1f0 + 3);
      } while (!bVar1);
      _DAT_2001e1f0[3] = _DAT_2001e1f0[3] & 0xffffffef;
LAB_08005216:
      uRam2001e224 = 2;
                    /* WARNING: Could not recover jumptable at 0x08005224. Too many branches */
                    /* WARNING: Treating indirect jump as call */
      (*pcRam2001e264)(&DAT_2001e1f0,sVar5);
      return;
    }
  }
  else if (((int)(uVar6 << 0x18) < 0) && ((uVar8 & 0x80) != 0)) {
    if (iRam2001e234 == 0x21) {
      if ((_DAT_2001e1f8 == 0x1000) && (_DAT_2001e200 == 0)) {
        _DAT_2001e1f0[1] = *puRam2001e210 & 0x1ff;
        puRam2001e210 = puRam2001e210 + 1;
      }
      else {
        uVar2 = *puRam2001e210;
        puRam2001e210 = (ushort *)((int)puRam2001e210 + 1);
        _DAT_2001e1f0[1] = (uint)(byte)uVar2;
      }
      sRam2001e216 = sRam2001e216 + -1;
      if (sRam2001e216 == 0) {
        puVar3[3] = puVar3[3] & 0xffffff7f;
        puVar3[3] = puVar3[3] | 0x40;
        return;
      }
    }
  }
  else if (((int)(uVar6 << 0x19) < 0) && ((uVar8 & 0x40) != 0)) {
    _DAT_2001e1f0[3] = _DAT_2001e1f0[3] & 0xffffffbf;
    iRam2001e234 = 0x20;
                    /* WARNING: Could not recover jumptable at 0x08004dc6. Too many branches */
                    /* WARNING: Treating indirect jump as call */
    (*pcRam2001e244)();
    return;
  }
  return;
}



/* 08007974 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void IRQ_71_Handler(void)

{
  byte *pbVar1;
  uint uVar2;
  int *piVar3;
  uint uVar4;
  uint uVar5;
  int iVar6;
  byte bVar7;
  uint uVar8;
  
  piVar3 = _DAT_2001e2f0;
  if (*_DAT_2001e2f0 << 0x1a < 0) {
    *_DAT_2001e2f0 = -0x21;
    uVar4 = piVar3[1];
    bVar7 = (byte)uVar4;
    switch(_DAT_2001ed90) {
    case 0:
      _DAT_2001ed90 = (uint)((uVar4 & 0xff) == 0x55);
      DAT_2001ed94 = 0x55;
      break;
    case 1:
      _DAT_2001ed90 = (uint)((uVar4 & 0xff) == 0x55) << 1;
      DAT_2001ed95 = 0x55;
      break;
    case 2:
      _DAT_2001ed90 = 3;
      DAT_2001ed96 = bVar7;
      break;
    case 3:
      if ((uVar4 & 0xff) < 8) {
        _DAT_2001ed90 = 4;
        DAT_2001ed97 = bVar7;
        break;
      }
    default:
      _DAT_2001ed90 = 0;
      break;
    case 4:
      _DAT_2001ed90 = (uint)DAT_2001ed97;
      _DAT_2001eda4 = 0;
      DAT_2001ed98 = bVar7;
      if (_DAT_2001ed90 != 6) {
        _DAT_2001ed90 = 5;
      }
      break;
    case 5:
      pbVar1 = (byte *)(_DAT_2001eda4 + 0x2001ed99);
      _DAT_2001eda4 = _DAT_2001eda4 + 1;
      *pbVar1 = bVar7;
      if (_DAT_2001eda4 + 3U == (uint)DAT_2001ed97) {
        _DAT_2001ed90 = 6;
      }
      break;
    case 6:
      uVar5 = (uint)DAT_2001ed97;
      if (uVar5 == 0) {
        bVar7 = 0xff;
      }
      else {
        if (uVar5 < 4) {
          bVar7 = 0;
          iVar6 = 2;
        }
        else {
          bVar7 = 0;
          uVar2 = 0;
          do {
            uVar8 = uVar2;
            bVar7 = *(char *)(uVar8 + 0x2001ed99) +
                    (&DAT_2001ed97)[uVar8] + bVar7 + (&DAT_2001ed96)[uVar8] + (&DAT_2001ed98)[uVar8]
            ;
            uVar2 = uVar8 + 4;
          } while ((uVar5 & 0xfc) != uVar8 + 4);
          iVar6 = uVar8 + 6;
        }
        if ((((DAT_2001ed97 & 3) != 0) && (bVar7 = bVar7 + (&DAT_2001ed94)[iVar6], (uVar5 & 3) != 1)
            ) && (bVar7 = bVar7 + (&DAT_2001ed95)[iVar6], (uVar5 & 3) != 2)) {
          bVar7 = bVar7 + (&DAT_2001ed96)[iVar6];
        }
        bVar7 = ~bVar7;
      }
      _DAT_2001ed90 = 0;
      if ((uint)bVar7 == (uVar4 & 0xff)) {
        FUN_0800d7a8(_DAT_2001c218);
        piVar3 = _DAT_2001e2f0;
      }
    }
  }
  if (*piVar3 << 0x19 < 0) {
    *piVar3 = -0x41;
    if (DAT_2001edbc == '\x01') {
      FUN_0800d7a8(_DAT_2001c218);
    }
    else {
      FUN_08001f84(0x40021000,0x100,0);
      FUN_08001f84(0x40021000,0x80,1);
    }
    uVar4 = _DAT_2001e2f0[3] & 0xffffffbf;
    piVar3 = _DAT_2001e2f0;
  }
  else {
    if (-1 < *piVar3 << 0x18) {
      return;
    }
    *piVar3 = -0x81;
    if (_DAT_2001edb8 < DAT_2001edab + 3) {
      pbVar1 = (byte *)(_DAT_2001edb8 + 0x2001eda8);
      _DAT_2001edb8 = _DAT_2001edb8 + 1;
      piVar3[1] = (uint)*pbVar1;
      return;
    }
    uVar4 = piVar3[3] & 0xffffff7f;
  }
  piVar3[3] = uVar4;
  return;
}



/* 08007b6c */

int FUN_08007b6c(int param_1,int param_2)

{
  int iVar1;
  
  if ((int)((uint)*(byte *)(param_1 + 0x491) << 0x18) < 0) {
    if ((int)((uint)*(byte *)(param_1 + 0x495) << 0x18) < 0) {
      if ((int)((uint)*(byte *)(param_1 + 0x499) << 0x18) < 0) {
        if ((int)((uint)*(byte *)(param_1 + 0x49d) << 0x18) < 0) {
          if ((int)((uint)*(byte *)(param_1 + 0x4a1) << 0x18) < 0) {
            if ((int)((uint)*(byte *)(param_1 + 0x4a5) << 0x18) < 0) {
              if ((int)((uint)*(byte *)(param_1 + 0x4a9) << 0x18) < 0) {
                if ((int)((uint)*(byte *)(param_1 + 0x4ad) << 0x18) < 0) {
                  if ((int)((uint)*(byte *)(param_1 + 0x4b1) << 0x18) < 0) {
                    if ((int)((uint)*(byte *)(param_1 + 0x4b5) << 0x18) < 0) {
                      if ((int)((uint)*(byte *)(param_1 + 0x4b9) << 0x18) < 0) {
                        if ((int)((uint)*(byte *)(param_1 + 0x4bd) << 0x18) < 0) {
                          if ((int)((uint)*(byte *)(param_1 + 0x4c1) << 0x18) < 0) {
                            if ((int)((uint)*(byte *)(param_1 + 0x4c5) << 0x18) < 0) {
                              if ((int)((uint)*(byte *)(param_1 + 0x4c9) << 0x18) < 0) {
                                if ((int)((uint)*(byte *)(param_1 + 0x4cd) << 0x18) < 0) {
                                  return 0xff;
                                }
                                iVar1 = 0xf;
                              }
                              else {
                                iVar1 = 0xe;
                              }
                            }
                            else {
                              iVar1 = 0xd;
                            }
                          }
                          else {
                            iVar1 = 0xc;
                          }
                        }
                        else {
                          iVar1 = 0xb;
                        }
                      }
                      else {
                        iVar1 = 10;
                      }
                    }
                    else {
                      iVar1 = 9;
                    }
                  }
                  else {
                    iVar1 = 8;
                  }
                }
                else {
                  iVar1 = 7;
                }
              }
              else {
                iVar1 = 6;
              }
            }
            else {
              iVar1 = 5;
            }
          }
          else {
            iVar1 = 4;
          }
        }
        else {
          iVar1 = 3;
        }
      }
      else {
        iVar1 = 2;
      }
    }
    else {
      iVar1 = 1;
    }
  }
  else {
    iVar1 = 0;
  }
  *(int *)(param_1 + 0x490 + iVar1 * 4) = param_2 + 0x8000;
  return iVar1;
}



/* 08007c40 */

undefined4 FUN_08007c40(void)

{
  FUN_08008cd0();
  return 0;
}



/* 08007c4c */

void FUN_08007c4c(int param_1,undefined2 param_2)

{
  if (*(int *)(param_1 + 8) == 1) {
    *(undefined2 *)(param_1 + 0x1c) = param_2;
    *(undefined4 *)(param_1 + 0x18) = 0x102;
    *(undefined2 *)(param_1 + 0x1e) = 0;
  }
  FUN_08007c90(param_1,0,0);
  return;
}



/* 08007c68 */

undefined4 FUN_08007c68(undefined4 param_1,undefined4 param_2,undefined4 param_3,undefined4 param_4)

{
  FUN_08008f1c(param_1,param_4,1,0,1,param_2,param_3,0);
  return 0;
}



/* 08007c90 */

undefined4 FUN_08007c90(undefined4 *param_1,undefined4 param_2,undefined2 param_3)

{
  char cVar1;
  undefined4 uVar2;
  int iVar3;
  undefined4 uVar4;
  undefined4 uVar5;
  undefined4 uVar6;
  
  if (param_1[2] != 2) {
    if (param_1[2] != 1) {
      return 1;
    }
    uVar5 = 1;
    uVar2 = 2;
    param_1[4] = param_2;
    *(undefined2 *)(param_1 + 5) = param_3;
    param_1[8] = 1;
LAB_08007caa:
    param_1[2] = uVar2;
    goto switchD_08007dc8_default;
  }
  switch(param_1[8]) {
  case 1:
    FUN_08007f08(param_1,param_1 + 6,*(undefined1 *)((int)param_1 + 0xd));
    uVar5 = 2;
    goto LAB_08007df0;
  case 2:
    iVar3 = FUN_08008d88(param_1,*(undefined1 *)((int)param_1 + 0xd));
    if (iVar3 == 4 || iVar3 == 2) {
LAB_08007d92:
      uVar5 = 0xb;
      goto LAB_08007d94;
    }
    if (iVar3 != 1) break;
    uVar5 = 3;
    uVar2 = 9;
    if (-1 < *(char *)(param_1 + 6)) {
      uVar5 = 5;
      uVar2 = 7;
    }
    if (*(short *)((int)param_1 + 0x1e) != 0) {
      uVar2 = uVar5;
    }
    param_1[8] = uVar2;
    goto LAB_08007d9c;
  case 3:
    *(short *)((int)param_1 + 0x16) = (short)param_1[0x134];
    FUN_08007c68(param_1,param_1[4],*(undefined2 *)(param_1 + 5),*(undefined1 *)(param_1 + 3));
    uVar5 = 4;
    goto LAB_08007df0;
  case 4:
    iVar3 = FUN_08008d88(param_1,*(undefined1 *)(param_1 + 3));
    if (iVar3 == 5) {
LAB_08007e34:
      uVar5 = 3;
LAB_08007e36:
      param_1[0x13b] = 3;
      FUN_0800d4f0(param_1[0x139],param_1 + 0x13b,0,0);
      param_1[2] = 1;
      param_1[8] = 0;
      goto switchD_08007dc8_default;
    }
    if (iVar3 == 4) goto LAB_08007d92;
    if (iVar3 == 1) {
LAB_08007d62:
      uVar5 = 9;
      goto LAB_08007d94;
    }
    break;
  case 5:
    uVar5 = 1;
    FUN_08007ed4(param_1,param_1[4],*(undefined2 *)(param_1 + 5),*(undefined1 *)((int)param_1 + 0xd)
                 ,1);
    *(short *)((int)param_1 + 0x16) = (short)param_1[0x134];
    param_1[8] = 6;
    goto switchD_08007dc8_default;
  case 6:
    uVar4 = FUN_08008d88(param_1,*(undefined1 *)((int)param_1 + 0xd));
    uVar5 = 1;
    uVar6 = 3;
    uVar2 = 0xc;
    switch(uVar4) {
    case 1:
      uVar5 = 7;
      break;
    case 2:
      uVar5 = 5;
      break;
    case 3:
      goto switchD_08007dc8_default;
    case 4:
      param_1[8] = 0xb;
      param_1[0x13b] = 3;
      FUN_0800d4f0(param_1[0x139],param_1 + 0x13b,0,0);
      goto LAB_08007eca;
    case 5:
switchD_08007dc8_caseD_5:
      param_1[8] = uVar2;
      uVar5 = uVar6;
      goto LAB_08007e36;
    default:
      goto switchD_08007dc8_default;
    }
LAB_08007d94:
    param_1[8] = uVar5;
LAB_08007d9c:
    param_1[0x13b] = 3;
    FUN_0800d4f0(param_1[0x139],param_1 + 0x13b,0,0);
    uVar5 = 1;
    goto switchD_08007dc8_default;
  case 7:
    FUN_08007c68(param_1,0,0,*(undefined1 *)(param_1 + 3));
    *(short *)((int)param_1 + 0x16) = (short)param_1[0x134];
    uVar5 = 8;
LAB_08007df0:
    param_1[8] = uVar5;
    uVar5 = 1;
    goto switchD_08007dc8_default;
  case 8:
    iVar3 = FUN_08008d88(param_1,*(undefined1 *)(param_1 + 3));
    if (iVar3 == 1) {
LAB_08007e2c:
      uVar6 = 0;
      uVar2 = 0xd;
      goto switchD_08007dc8_caseD_5;
    }
    if (iVar3 == 5) goto LAB_08007e34;
    if (iVar3 == 4) goto LAB_08007d92;
    break;
  case 9:
    uVar5 = 1;
    FUN_08007ed4(param_1,0,0,*(undefined1 *)((int)param_1 + 0xd),1);
    *(short *)((int)param_1 + 0x16) = (short)param_1[0x134];
    param_1[8] = 10;
    goto switchD_08007dc8_default;
  case 10:
    iVar3 = FUN_08008d88(param_1,*(undefined1 *)((int)param_1 + 0xd));
    if (iVar3 == 1) goto LAB_08007e2c;
    if (iVar3 == 4) goto LAB_08007d92;
    if (iVar3 == 2) goto LAB_08007d62;
    break;
  case 0xb:
    cVar1 = *(char *)(param_1 + 9);
    *(byte *)(param_1 + 9) = cVar1 + 1U;
    if ((byte)(cVar1 + 1U) < 3) {
      uVar5 = 1;
      param_1[8] = 1;
      param_1[2] = 1;
      goto switchD_08007dc8_default;
    }
    (*(code *)param_1[0x138])(param_1,6);
    *(undefined1 *)(param_1 + 9) = 0;
    FUN_0800802c(param_1,*(undefined1 *)((int)param_1 + 0xd));
    FUN_0800802c(param_1,*(undefined1 *)(param_1 + 3));
    *param_1 = 0;
LAB_08007eca:
    uVar2 = 1;
    uVar5 = 2;
    goto LAB_08007caa;
  }
  uVar5 = 1;
switchD_08007dc8_default:
  param_1[0x13b] = 3;
  FUN_0800d4f0(param_1[0x139],param_1 + 0x13b,0,0);
  return uVar5;
}



/* 08007ed4 */

undefined4
FUN_08007ed4(int param_1,undefined4 param_2,undefined4 param_3,undefined4 param_4,undefined4 param_5
            )

{
  if (*(char *)(param_1 + 0x429) != '\0') {
    param_5 = 0;
  }
  FUN_08008f1c(param_1,param_4,0,0,1,param_2,param_3,param_5);
  return 0;
}



/* 08007f08 */

undefined4 FUN_08007f08(undefined4 param_1,undefined4 param_2,undefined4 param_3)

{
  FUN_08008f1c(param_1,param_3,0,0,0,param_2,8,0);
  return 0;
}



/* 08007f2c */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void thunk_FUN_08001db0(uint param_1)

{
  int iVar1;
  int iVar2;
  
  iVar1 = FUN_08001f90();
  if (param_1 != 0xffffffff) {
    param_1 = param_1 + _DAT_2001c010;
  }
  do {
    iVar2 = FUN_08001f90();
  } while ((uint)(iVar2 - iVar1) < param_1);
  return;
}



/* 08007f30 */

undefined1 FUN_08007f30(int param_1,uint param_2,uint param_3,uint param_4)

{
  undefined1 uVar1;
  uint uVar2;
  
  if (param_2 == 0xff) {
    if (param_3 == 0xff) {
      if ((param_4 != 0xff) && (*(byte *)(param_1 + 0x455) != param_4)) {
        uVar1 = 0xff;
        if (*(byte *)(param_1 + 0x46f) == param_4) {
          uVar1 = 1;
        }
        return uVar1;
      }
      return 0;
    }
    if (param_4 == 0xff) {
      if (*(byte *)(param_1 + 0x454) == param_3) {
        return 0;
      }
      uVar1 = 0xff;
      if (*(byte *)(param_1 + 0x46e) == param_3) {
        uVar1 = 1;
      }
      return uVar1;
    }
    if ((*(byte *)(param_1 + 0x454) == param_3) && (*(byte *)(param_1 + 0x455) == param_4)) {
      return 0;
    }
  }
  else {
    uVar2 = (uint)*(byte *)(param_1 + 0x453);
    if (param_3 == 0xff) {
      if (param_4 == 0xff) {
        if (uVar2 == param_2) {
          return 0;
        }
        uVar1 = 0xff;
        if (*(byte *)(param_1 + 0x46d) == param_2) {
          uVar1 = 1;
        }
        return uVar1;
      }
      if ((uVar2 == param_2) && (*(byte *)(param_1 + 0x455) == param_4)) {
        return 0;
      }
      if (*(byte *)(param_1 + 0x46d) != param_2) {
        return 0xff;
      }
      goto LAB_08008014;
    }
    if (param_4 == 0xff) {
      if ((uVar2 == param_2) && (*(byte *)(param_1 + 0x454) == param_3)) {
        return 0;
      }
      if (*(byte *)(param_1 + 0x46d) != param_2) {
        return 0xff;
      }
      if (*(byte *)(param_1 + 0x46e) == param_3) {
        return 1;
      }
      return 0xff;
    }
    if (((uVar2 == param_2) && (*(byte *)(param_1 + 0x454) == param_3)) &&
       (*(byte *)(param_1 + 0x455) == param_4)) {
      return 0;
    }
    if (*(byte *)(param_1 + 0x46d) != param_2) {
      return 0xff;
    }
  }
  if (*(byte *)(param_1 + 0x46e) != param_3) {
    return 0xff;
  }
LAB_08008014:
  if (*(byte *)(param_1 + 0x46f) != param_4) {
    return 0xff;
  }
  return 1;
}



/* 0800802c */

undefined4 FUN_0800802c(int param_1,uint param_2)

{
  if (param_2 < 0x10) {
    param_1 = param_1 + param_2 * 4;
    *(uint *)(param_1 + 0x490) = *(uint *)(param_1 + 0x490) & 0x7fff;
  }
  return 0;
}



/* 08008044 */

void FUN_08008044(int param_1,byte param_2,uint param_3,undefined4 param_4,undefined2 param_5)

{
  undefined2 uVar1;
  
  if (*(int *)(param_1 + 8) == 1) {
    *(byte *)(param_1 + 0x18) = param_2 | 0x80;
    *(undefined1 *)(param_1 + 0x19) = 6;
    uVar1 = 0;
    *(short *)(param_1 + 0x1a) = (short)param_3;
    if ((param_3 & 0xffffff00) == 0x300) {
      uVar1 = 0x409;
    }
    *(undefined2 *)(param_1 + 0x1c) = uVar1;
    *(undefined2 *)(param_1 + 0x1e) = param_5;
  }
  FUN_08007c90(param_1,param_4);
  return;
}



/* 08008080 */

byte * FUN_08008080(byte *param_1,short *param_2)

{
  byte bVar1;
  
  bVar1 = *param_1;
  *param_2 = *param_2 + (ushort)bVar1;
  return param_1 + bVar1;
}



/* 0800808c */

int FUN_0800808c(int param_1,uint param_2)

{
  byte bVar1;
  byte bVar2;
  byte bVar3;
  byte bVar4;
  byte bVar5;
  char cVar6;
  ushort uVar7;
  byte bVar8;
  int iVar9;
  byte bVar10;
  uint uVar11;
  int iVar12;
  int iVar13;
  byte *pbVar14;
  byte bVar15;
  uint uVar16;
  uint uVar17;
  uint uVar18;
  byte bVar19;
  bool bVar20;
  
  if (0x200 < param_2) {
    return 3;
  }
  pbVar14 = (byte *)(param_1 + 0x28);
  if (*(int *)(param_1 + 8) == 1) {
    *(undefined2 *)(param_1 + 0x18) = 0x680;
    *(undefined4 *)(param_1 + 0x1a) = 0x200;
    *(short *)(param_1 + 0x1e) = (short)param_2;
  }
  iVar9 = FUN_08007c90(param_1,pbVar14,param_2);
  if (iVar9 != 0) {
    return iVar9;
  }
  if (*(char *)(param_1 + 0x28) != '\t') {
    *pbVar14 = 9;
  }
  *(undefined1 *)(param_1 + 0x444) = 9;
  *(undefined1 *)(param_1 + 0x445) = *(undefined1 *)(param_1 + 0x29);
  if (*(byte *)(param_1 + 0x2b) < 2) {
    uVar16 = (uint)CONCAT11(*(byte *)(param_1 + 0x2b),*(undefined1 *)(param_1 + 0x2a));
  }
  else {
    uVar16 = 0x200;
  }
  bVar10 = *(byte *)(param_1 + 0x2c);
  *(short *)(param_1 + 0x446) = (short)uVar16;
  *(byte *)(param_1 + 0x448) = bVar10;
  *(undefined4 *)(param_1 + 0x449) = *(undefined4 *)(param_1 + 0x2d);
  if (param_2 < 10) {
    return 0;
  }
  iVar9 = 0;
  if (uVar16 < 10) {
    bVar15 = 0;
  }
  else {
    uVar11 = 0;
    bVar15 = 0;
    uVar18 = 9;
    do {
      bVar1 = *pbVar14;
      pbVar14 = pbVar14 + bVar1;
      uVar18 = uVar18 + bVar1;
      if (pbVar14[1] == 4) {
        if (*pbVar14 != 9) {
          *pbVar14 = 9;
        }
        iVar13 = uVar11 * 0x1a + param_1 + 0x44e;
        *(undefined1 *)(param_1 + 0x44e + uVar11 * 0x1a) = 9;
        *(byte *)(iVar13 + 1) = pbVar14[1];
        *(byte *)(iVar13 + 2) = pbVar14[2];
        *(byte *)(iVar13 + 3) = pbVar14[3];
        uVar17 = (uint)pbVar14[4];
        uVar11 = uVar17;
        if (1 < uVar17) {
          uVar11 = 2;
        }
        *(char *)(iVar13 + 4) = (char)uVar11;
        bVar1 = pbVar14[5];
        *(byte *)(iVar13 + 5) = bVar1;
        bVar2 = pbVar14[6];
        *(byte *)(iVar13 + 6) = bVar2;
        bVar3 = pbVar14[7];
        *(byte *)(iVar13 + 7) = bVar3;
        *(byte *)(iVar13 + 8) = pbVar14[8];
        if (uVar17 != 0) {
          uVar17 = 0;
          bVar19 = 0;
          do {
            if (uVar16 <= (uVar18 & 0xffff)) {
              return 3;
            }
            bVar5 = *pbVar14;
            pbVar14 = pbVar14 + bVar5;
            if (pbVar14[1] == 5) {
              if (bVar1 == 1 && (bVar2 & 0xfe) == 2) {
                bVar8 = *pbVar14;
                if (bVar3 == 0) {
                  bVar20 = bVar8 != 9;
                  bVar8 = 9;
                  bVar4 = 9;
                  if (bVar20) goto LAB_08008206;
                }
              }
              else {
                bVar4 = 7;
LAB_08008206:
                bVar8 = bVar4;
                *pbVar14 = bVar8;
              }
              *(byte *)(iVar13 + 10 + uVar17 * 8) = bVar8;
              iVar12 = iVar13 + 10 + uVar17 * 8;
              *(byte *)(iVar12 + 1) = pbVar14[1];
              cVar6 = *(char *)(param_1 + 0x429);
              *(byte *)(iVar12 + 2) = pbVar14[2];
              bVar4 = pbVar14[3];
              *(byte *)(iVar12 + 3) = bVar4;
              bVar8 = pbVar14[5];
              uVar7 = *(ushort *)(pbVar14 + 4);
              *(ushort *)(iVar12 + 4) = uVar7;
              uVar17 = (uint)pbVar14[6];
              iVar9 = 0;
              if ((ushort)(uVar7 - 0x201) < 0xfe00) {
                iVar9 = 3;
              }
              *(byte *)(iVar12 + 6) = pbVar14[6];
              if (cVar6 == '\x02') {
                if ((bVar4 & 3) == 3) {
                  if (8 < uVar7) {
                    iVar9 = 3;
                  }
                  if (uVar17 == 0) {
                    iVar9 = 3;
                  }
                }
                else {
                  if ((bVar4 & 3) != 0) goto LAB_080082a2;
                  iVar9 = 0;
                  if (uVar7 != 8) {
                    iVar9 = 3;
                  }
                }
              }
              else if (cVar6 == '\x01') {
                switch(bVar4 & 3) {
                default:
                  if (0x40 < uVar7) {
                    iVar9 = 3;
                  }
                  break;
                case 1:
                  if (0x40 < uVar7) {
                    iVar9 = 3;
                  }
                  if (uVar17 - 0x11 < 0xfffffff0) {
                    iVar9 = 3;
                  }
                  break;
                case 3:
                  if (3 < bVar8) {
                    iVar9 = 3;
                  }
                  if (uVar17 == 0) {
                    iVar9 = 3;
                  }
                }
              }
              else if (cVar6 == '\0') {
                switch(bVar4 & 3) {
                case 0:
                  if (0x40 < uVar7) {
                    iVar9 = 3;
                  }
                  break;
                default:
                  if (uVar17 - 0x11 < 0xfffffff0) {
                    iVar9 = 3;
                  }
                  break;
                case 2:
                  if (0x200 < uVar7) {
                    iVar9 = 3;
                  }
                }
              }
              else {
LAB_080082a2:
                iVar9 = 3;
              }
              bVar19 = bVar19 + 1;
            }
            uVar17 = (uint)bVar19;
            uVar18 = uVar18 + bVar5;
          } while (uVar17 < uVar11);
        }
        bVar15 = bVar15 + 1;
      }
      uVar11 = (uint)bVar15;
    } while ((uVar11 < 2) && ((uVar18 & 0xffff) < uVar16));
  }
  if (1 < bVar10) {
    bVar10 = 2;
  }
  if (bVar15 < bVar10) {
    iVar9 = 3;
  }
  return iVar9;
}



/* 08008096 */

int FUN_08008096(int param_1,uint param_2)

{
  byte bVar1;
  byte bVar2;
  byte bVar3;
  byte bVar4;
  byte bVar5;
  char cVar6;
  ushort uVar7;
  byte bVar8;
  int iVar9;
  byte bVar10;
  uint uVar11;
  int iVar12;
  int iVar13;
  byte *pbVar14;
  byte bVar15;
  uint uVar16;
  uint uVar17;
  uint uVar18;
  byte bVar19;
  bool bVar20;
  
  pbVar14 = (byte *)(param_1 + 0x28);
  if (*(int *)(param_1 + 8) == 1) {
    *(undefined2 *)(param_1 + 0x18) = 0x680;
    *(undefined4 *)(param_1 + 0x1a) = 0x200;
    *(short *)(param_1 + 0x1e) = (short)param_2;
  }
  iVar9 = FUN_08007c90(param_1,pbVar14,param_2);
  if (iVar9 != 0) {
    return iVar9;
  }
  if (*(char *)(param_1 + 0x28) != '\t') {
    *pbVar14 = 9;
  }
  *(undefined1 *)(param_1 + 0x444) = 9;
  *(undefined1 *)(param_1 + 0x445) = *(undefined1 *)(param_1 + 0x29);
  if (*(byte *)(param_1 + 0x2b) < 2) {
    uVar16 = (uint)CONCAT11(*(byte *)(param_1 + 0x2b),*(undefined1 *)(param_1 + 0x2a));
  }
  else {
    uVar16 = 0x200;
  }
  bVar10 = *(byte *)(param_1 + 0x2c);
  *(short *)(param_1 + 0x446) = (short)uVar16;
  *(byte *)(param_1 + 0x448) = bVar10;
  *(undefined4 *)(param_1 + 0x449) = *(undefined4 *)(param_1 + 0x2d);
  if (param_2 < 10) {
    return 0;
  }
  iVar9 = 0;
  if (uVar16 < 10) {
    bVar15 = 0;
  }
  else {
    uVar11 = 0;
    bVar15 = 0;
    uVar18 = 9;
    do {
      bVar1 = *pbVar14;
      pbVar14 = pbVar14 + bVar1;
      uVar18 = uVar18 + bVar1;
      if (pbVar14[1] == 4) {
        if (*pbVar14 != 9) {
          *pbVar14 = 9;
        }
        iVar13 = uVar11 * 0x1a + param_1 + 0x44e;
        *(undefined1 *)(param_1 + 0x44e + uVar11 * 0x1a) = 9;
        *(byte *)(iVar13 + 1) = pbVar14[1];
        *(byte *)(iVar13 + 2) = pbVar14[2];
        *(byte *)(iVar13 + 3) = pbVar14[3];
        uVar17 = (uint)pbVar14[4];
        uVar11 = uVar17;
        if (1 < uVar17) {
          uVar11 = 2;
        }
        *(char *)(iVar13 + 4) = (char)uVar11;
        bVar1 = pbVar14[5];
        *(byte *)(iVar13 + 5) = bVar1;
        bVar2 = pbVar14[6];
        *(byte *)(iVar13 + 6) = bVar2;
        bVar3 = pbVar14[7];
        *(byte *)(iVar13 + 7) = bVar3;
        *(byte *)(iVar13 + 8) = pbVar14[8];
        if (uVar17 != 0) {
          uVar17 = 0;
          bVar19 = 0;
          do {
            if (uVar16 <= (uVar18 & 0xffff)) {
              return 3;
            }
            bVar5 = *pbVar14;
            pbVar14 = pbVar14 + bVar5;
            if (pbVar14[1] == 5) {
              if (bVar1 == 1 && (bVar2 & 0xfe) == 2) {
                bVar8 = *pbVar14;
                if (bVar3 == 0) {
                  bVar20 = bVar8 != 9;
                  bVar8 = 9;
                  bVar4 = 9;
                  if (bVar20) goto LAB_08008206;
                }
              }
              else {
                bVar4 = 7;
LAB_08008206:
                bVar8 = bVar4;
                *pbVar14 = bVar8;
              }
              *(byte *)(iVar13 + 10 + uVar17 * 8) = bVar8;
              iVar12 = iVar13 + 10 + uVar17 * 8;
              *(byte *)(iVar12 + 1) = pbVar14[1];
              cVar6 = *(char *)(param_1 + 0x429);
              *(byte *)(iVar12 + 2) = pbVar14[2];
              bVar4 = pbVar14[3];
              *(byte *)(iVar12 + 3) = bVar4;
              bVar8 = pbVar14[5];
              uVar7 = *(ushort *)(pbVar14 + 4);
              *(ushort *)(iVar12 + 4) = uVar7;
              uVar17 = (uint)pbVar14[6];
              iVar9 = 0;
              if ((ushort)(uVar7 - 0x201) < 0xfe00) {
                iVar9 = 3;
              }
              *(byte *)(iVar12 + 6) = pbVar14[6];
              if (cVar6 == '\x02') {
                if ((bVar4 & 3) == 3) {
                  if (8 < uVar7) {
                    iVar9 = 3;
                  }
                  if (uVar17 == 0) {
                    iVar9 = 3;
                  }
                }
                else {
                  if ((bVar4 & 3) != 0) goto LAB_080082a2;
                  iVar9 = 0;
                  if (uVar7 != 8) {
                    iVar9 = 3;
                  }
                }
              }
              else if (cVar6 == '\x01') {
                switch(bVar4 & 3) {
                default:
                  if (0x40 < uVar7) {
                    iVar9 = 3;
                  }
                  break;
                case 1:
                  if (0x40 < uVar7) {
                    iVar9 = 3;
                  }
                  if (uVar17 - 0x11 < 0xfffffff0) {
                    iVar9 = 3;
                  }
                  break;
                case 3:
                  if (3 < bVar8) {
                    iVar9 = 3;
                  }
                  if (uVar17 == 0) {
                    iVar9 = 3;
                  }
                }
              }
              else if (cVar6 == '\0') {
                switch(bVar4 & 3) {
                case 0:
                  if (0x40 < uVar7) {
                    iVar9 = 3;
                  }
                  break;
                default:
                  if (uVar17 - 0x11 < 0xfffffff0) {
                    iVar9 = 3;
                  }
                  break;
                case 2:
                  if (0x200 < uVar7) {
                    iVar9 = 3;
                  }
                }
              }
              else {
LAB_080082a2:
                iVar9 = 3;
              }
              bVar19 = bVar19 + 1;
            }
            uVar17 = (uint)bVar19;
            uVar18 = uVar18 + bVar5;
          } while (uVar17 < uVar11);
        }
        bVar15 = bVar15 + 1;
      }
      uVar11 = (uint)bVar15;
    } while ((uVar11 < 2) && ((uVar18 & 0xffff) < uVar16));
  }
  if (1 < bVar10) {
    bVar10 = 2;
  }
  if (bVar15 < bVar10) {
    iVar9 = 3;
  }
  return iVar9;
}



/* 0800832c */

int FUN_0800832c(int param_1,uint param_2)

{
  uint uVar1;
  int iVar2;
  uint uVar3;
  
  if (0x200 < param_2) {
    return 3;
  }
  if (*(int *)(param_1 + 8) == 1) {
    *(undefined2 *)(param_1 + 0x18) = 0x680;
    *(undefined4 *)(param_1 + 0x1a) = 0x100;
    *(short *)(param_1 + 0x1e) = (short)param_2;
  }
  iVar2 = FUN_08007c90(param_1,param_1 + 0x228,param_2);
  if (iVar2 != 0) {
    return iVar2;
  }
  *(undefined4 *)(param_1 + 0x432) = *(undefined4 *)(param_1 + 0x228);
  *(undefined2 *)(param_1 + 0x437) = *(undefined2 *)(param_1 + 0x22d);
  *(undefined1 *)(param_1 + 0x436) = *(undefined1 *)(param_1 + 0x22c);
  uVar3 = (uint)*(byte *)(param_1 + 0x22f);
  *(byte *)(param_1 + 0x439) = *(byte *)(param_1 + 0x22f);
  if (*(byte *)(param_1 + 0x429) < 2) {
    uVar1 = uVar3 - 8 >> 3;
    if ((7 < (uVar1 | uVar3 << 0x1d)) || ((0x8bU >> (uVar1 & 0xff) & 1) == 0)) {
LAB_080083aa:
      *(undefined1 *)(param_1 + 0x439) = 8;
    }
  }
  else {
    if (*(byte *)(param_1 + 0x429) != 2) {
      iVar2 = 3;
      goto LAB_080083b6;
    }
    if (uVar3 != 8) goto LAB_080083aa;
  }
  iVar2 = 0;
LAB_080083b6:
  if (param_2 < 9) {
    return iVar2;
  }
  *(undefined2 *)(param_1 + 0x43a) = *(undefined2 *)(param_1 + 0x230);
  *(undefined1 *)(param_1 + 0x440) = *(undefined1 *)(param_1 + 0x236);
  *(undefined4 *)(param_1 + 0x43c) = *(undefined4 *)(param_1 + 0x232);
  *(undefined2 *)(param_1 + 0x441) = *(undefined2 *)(param_1 + 0x237);
  *(undefined1 *)(param_1 + 0x443) = *(undefined1 *)(param_1 + 0x239);
  return iVar2;
}



/* 08008336 */

int FUN_08008336(int param_1,uint param_2)

{
  uint uVar1;
  int iVar2;
  uint uVar3;
  
  if (*(int *)(param_1 + 8) == 1) {
    *(undefined2 *)(param_1 + 0x18) = 0x680;
    *(undefined4 *)(param_1 + 0x1a) = 0x100;
    *(short *)(param_1 + 0x1e) = (short)param_2;
  }
  iVar2 = FUN_08007c90(param_1,param_1 + 0x228,param_2);
  if (iVar2 != 0) {
    return iVar2;
  }
  *(undefined4 *)(param_1 + 0x432) = *(undefined4 *)(param_1 + 0x228);
  *(undefined2 *)(param_1 + 0x437) = *(undefined2 *)(param_1 + 0x22d);
  *(undefined1 *)(param_1 + 0x436) = *(undefined1 *)(param_1 + 0x22c);
  uVar3 = (uint)*(byte *)(param_1 + 0x22f);
  *(byte *)(param_1 + 0x439) = *(byte *)(param_1 + 0x22f);
  if (*(byte *)(param_1 + 0x429) < 2) {
    uVar1 = uVar3 - 8 >> 3;
    if ((7 < (uVar1 | uVar3 << 0x1d)) || ((0x8bU >> (uVar1 & 0xff) & 1) == 0)) {
LAB_080083aa:
      *(undefined1 *)(param_1 + 0x439) = 8;
    }
  }
  else {
    if (*(byte *)(param_1 + 0x429) != 2) {
      iVar2 = 3;
      goto LAB_080083b6;
    }
    if (uVar3 != 8) goto LAB_080083aa;
  }
  iVar2 = 0;
LAB_080083b6:
  if (8 < param_2) {
    *(undefined2 *)(param_1 + 0x43a) = *(undefined2 *)(param_1 + 0x230);
    *(undefined1 *)(param_1 + 0x440) = *(undefined1 *)(param_1 + 0x236);
    *(undefined4 *)(param_1 + 0x43c) = *(undefined4 *)(param_1 + 0x232);
    *(undefined2 *)(param_1 + 0x441) = *(undefined2 *)(param_1 + 0x237);
    *(undefined1 *)(param_1 + 0x443) = *(undefined1 *)(param_1 + 0x239);
    return iVar2;
  }
  return iVar2;
}



/* 080083e8 */

int FUN_080083e8(int param_1,short param_2,undefined1 *param_3,uint param_4)

{
  int iVar1;
  uint uVar2;
  uint uVar3;
  uint uVar4;
  
  iVar1 = 3;
  if (param_3 != (undefined1 *)0x0) {
    if (0x200 < param_4) {
      return 3;
    }
    if (*(int *)(param_1 + 8) == 1) {
      *(short *)(param_1 + 0x1a) = param_2 + 0x300;
      *(undefined2 *)(param_1 + 0x18) = 0x680;
      *(undefined2 *)(param_1 + 0x1c) = 0x409;
      *(short *)(param_1 + 0x1e) = (short)param_4;
    }
    iVar1 = FUN_08007c90(param_1,param_1 + 0x228,param_4);
    if (iVar1 == 0) {
      if (*(char *)(param_1 + 0x229) != '\x03') {
        return 0;
      }
      uVar2 = *(byte *)(param_1 + 0x228) - 2;
      if (param_4 < uVar2) {
        uVar2 = param_4;
      }
      uVar2 = uVar2 & 0xffff;
      if (uVar2 != 0) {
        param_1 = param_1 + 0x22a;
        uVar3 = 0;
        do {
          *param_3 = *(undefined1 *)(param_1 + uVar3);
          if (uVar2 <= uVar3 + 2) {
            param_3[1] = 0;
            return 0;
          }
          param_3[1] = *(undefined1 *)(param_1 + uVar3 + 2);
          if (uVar2 <= uVar3 + 4) {
            param_3[2] = 0;
            return 0;
          }
          uVar4 = uVar3 + 6;
          param_3[2] = *(undefined1 *)(param_1 + uVar3 + 4);
          if (uVar2 <= uVar4) {
            param_3[3] = 0;
            return 0;
          }
          uVar3 = uVar3 + 8 & 0xffff;
          param_3[3] = *(undefined1 *)(param_1 + uVar4);
          param_3 = param_3 + 4;
        } while (uVar3 < uVar2);
      }
      *param_3 = 0;
      return 0;
    }
  }
  return iVar1;
}



/* 080084a4 */

undefined4 FUN_080084a4(int param_1)

{
  ushort uVar1;
  undefined4 uVar2;
  undefined1 *puVar3;
  int iVar4;
  code *pcVar5;
  int iVar6;
  ushort local_12;
  
  iVar6 = *(int *)(*(int *)(param_1 + 0x488) + 0x1c);
  uVar2 = 1;
  switch(*(undefined4 *)(iVar6 + 0xc)) {
  case 0:
  case 3:
    uVar1 = *(ushort *)(param_1 + 0x2a);
    if (9 < uVar1) {
      puVar3 = (undefined1 *)(param_1 + 0x28);
      local_12 = 9;
      do {
        if (uVar1 <= local_12) goto LAB_08008514;
        puVar3 = (undefined1 *)FUN_08008080(puVar3,&local_12);
      } while (puVar3[1] != '!');
      *(undefined1 *)(iVar6 + 0x2e) = *puVar3;
      *(undefined1 *)(iVar6 + 0x2f) = puVar3[1];
      *(undefined2 *)(iVar6 + 0x30) = *(undefined2 *)(puVar3 + 2);
      *(undefined1 *)(iVar6 + 0x32) = puVar3[4];
      *(undefined1 *)(iVar6 + 0x33) = puVar3[5];
      *(undefined1 *)(iVar6 + 0x34) = puVar3[6];
      *(undefined2 *)(iVar6 + 0x36) = *(undefined2 *)(puVar3 + 7);
    }
LAB_08008514:
    uVar2 = 2;
    goto LAB_0800853e;
  default:
    goto switchD_080084b8_caseD_1;
  case 2:
    iVar4 = FUN_080087b0(param_1,*(undefined2 *)(iVar6 + 0x36));
    if (iVar4 != 3) {
      if (iVar4 != 0) {
        return 1;
      }
      uVar2 = 4;
      goto LAB_0800853e;
    }
    break;
  case 4:
    iVar4 = FUN_08008bb0(param_1,0x32,0);
    if ((iVar4 != 3) && (iVar4 != 0)) {
      return 1;
    }
    uVar2 = 5;
LAB_0800853e:
    *(undefined4 *)(iVar6 + 0xc) = uVar2;
    return 1;
  case 5:
    iVar4 = FUN_08008bc8(param_1,0);
    if (iVar4 != 3) {
      if (iVar4 != 0) {
        return 1;
      }
      pcVar5 = *(code **)(param_1 + 0x4e0);
      *(undefined4 *)(iVar6 + 0xc) = 1;
      (*pcVar5)(param_1,2);
      return 0;
    }
  }
  uVar2 = 2;
switchD_080084b8_caseD_1:
  return uVar2;
}



/* 08008574 */

void FUN_08008574(undefined4 param_1)

{
  int iVar1;
  undefined2 *puVar2;
  undefined2 local_10;
  undefined1 local_e;
  undefined4 local_d;
  
  iVar1 = FUN_08008718();
  if ((iVar1 == 0xff) && (puVar2 = (undefined2 *)FUN_08008744(param_1), puVar2 != (undefined2 *)0x0)
     ) {
    local_10 = *puVar2;
    local_e = *(undefined1 *)(puVar2 + 1);
    local_d = *(undefined4 *)((int)puVar2 + 3);
    FUN_0800e274(0x2001e468,8,&local_10,7);
  }
  return;
}



/* 080085b4 */

void FUN_080085b4(undefined4 *param_1,undefined4 param_2,undefined2 param_3)

{
  *(undefined1 *)((int)param_1 + 10) = 0;
  *(undefined2 *)(param_1 + 2) = param_3;
  *param_1 = param_2;
  param_1[1] = 0;
  return;
}



/* 080085c0 */

uint FUN_080085c0(int *param_1,undefined1 *param_2,uint param_3)

{
  ushort uVar1;
  uint uVar2;
  ushort uVar3;
  uint uVar4;
  
  if (*(char *)((int)param_1 + 10) != '\0') {
    *(undefined1 *)((int)param_1 + 10) = 0;
    return param_3 & 0xffff;
  }
  *(undefined1 *)((int)param_1 + 10) = 1;
  if (param_3 == 0) {
    *(undefined1 *)((int)param_1 + 10) = 0;
    return 0;
  }
  uVar3 = *(ushort *)((int)param_1 + 6);
  uVar4 = 0;
  do {
    uVar2 = uVar4;
    if ((uint)uVar3 == (uint)*(ushort *)(param_1 + 1)) break;
    uVar4 = uVar4 + 1;
    *param_2 = *(undefined1 *)(*param_1 + (uint)uVar3);
    uVar1 = *(short *)((int)param_1 + 6) + 1;
    uVar3 = 0;
    if (uVar1 != *(ushort *)(param_1 + 2)) {
      uVar3 = uVar1;
    }
    *(ushort *)((int)param_1 + 6) = uVar3;
    param_2 = param_2 + 1;
    uVar2 = param_3;
  } while (uVar4 < param_3);
  *(undefined1 *)((int)param_1 + 10) = 0;
  return uVar2 & 0xffff;
}



/* 08008630 */

uint FUN_08008630(int *param_1,undefined1 *param_2,uint param_3)

{
  uint uVar1;
  ushort uVar2;
  ushort uVar3;
  
  if (*(char *)((int)param_1 + 10) == '\0') {
    *(undefined1 *)((int)param_1 + 10) = 1;
    if (param_3 == 0) {
      *(undefined1 *)((int)param_1 + 10) = 0;
      return 0;
    }
    uVar2 = *(ushort *)(param_1 + 1);
    uVar1 = 0;
    do {
      if ((uVar2 + 1 == (uint)*(ushort *)((int)param_1 + 6)) ||
         ((*(ushort *)((int)param_1 + 6) == 0 && (uVar2 + 1 == (uint)*(ushort *)(param_1 + 2))))) {
        *(undefined1 *)((int)param_1 + 10) = 0;
        return uVar1 & 0xffff;
      }
      *(undefined1 *)(*param_1 + (uint)uVar2) = *param_2;
      uVar1 = uVar1 + 1;
      uVar3 = (short)param_1[1] + 1;
      uVar2 = 0;
      if (uVar3 != *(ushort *)(param_1 + 2)) {
        uVar2 = uVar3;
      }
      *(ushort *)(param_1 + 1) = uVar2;
      param_2 = param_2 + 1;
    } while (uVar1 < param_3);
  }
  *(undefined1 *)((int)param_1 + 10) = 0;
  return param_3 & 0xffff;
}



/* 08008718 */

undefined4 FUN_08008718(int *param_1)

{
  char cVar1;
  undefined4 uVar2;
  
  uVar2 = 0xff;
  if (*param_1 != 0xb) {
    return 0xff;
  }
  cVar1 = *(char *)((int)param_1 + (short)(ushort)*(byte *)(param_1 + 0x10c) * 0x1a + 0x455);
  if (cVar1 == '\x02') {
    uVar2 = 1;
  }
  if (cVar1 == '\x01') {
    uVar2 = 2;
  }
  return uVar2;
}



/* 08008744 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined1 * FUN_08008744(int param_1)

{
  uint uVar1;
  undefined1 *puVar2;
  int iVar3;
  
  iVar3 = *(int *)(*(int *)(param_1 + 0x488) + 0x1c);
  if (*(short *)(iVar3 + 0x20) == 0) {
    return (undefined1 *)0x0;
  }
  uVar1 = FUN_080085c0(iVar3 + 0x10,&DAT_2001c3a4);
  puVar2 = (undefined1 *)0x0;
  if (uVar1 == *(ushort *)(iVar3 + 0x20)) {
    if (DAT_2001c3b8 == '\x02') {
      return (undefined1 *)0x0;
    }
    _DAT_2001c39c = (ushort)(((uint)_DAT_2001c3aa << 0x18) >> 0x10) | _DAT_2001c3aa >> 8;
    DAT_2001c39e = ~DAT_2001c3a9 & 0xf;
    DAT_2001c39f = DAT_2001c3a5 ^ 0x80;
    DAT_2001c3a0 = DAT_2001c3a6 ^ 0x7f;
    bRam2001c3a1 = DAT_2001c3a7 ^ 0x80;
    bRam2001c3a2 = DAT_2001c3a8 ^ 0x7f;
    puVar2 = &DAT_2001c39c;
  }
  return puVar2;
}



/* 080087b0 */

void FUN_080087b0(int param_1,uint param_2)

{
  if (param_2 < 0x201) {
    FUN_08008044(param_1,1,0x2200,param_1 + 0x228,param_2);
    return;
  }
  return;
}



/* 080087ba */

void FUN_080087ba(int param_1,undefined4 param_2)

{
  FUN_08008044(param_1,1,0x2200,param_1 + 0x228,param_2);
  return;
}



/* 080087d8 */

void FUN_080087d8(int param_1,short param_2,ushort param_3,undefined4 param_4,undefined4 param_5)

{
  *(ushort *)(param_1 + 0x1a) = param_3 | param_2 << 8;
  *(undefined2 *)(param_1 + 0x18) = 0x1a1;
  *(undefined2 *)(param_1 + 0x1c) = 0;
  *(short *)(param_1 + 0x1e) = (short)param_5;
  FUN_08007c90(param_1,param_4,param_5);
  return;
}



/* 08008800 */

undefined4 FUN_08008800(int param_1)

{
  char *pcVar1;
  
  pcVar1 = *(char **)(*(int *)(param_1 + 0x488) + 0x1c);
  if (pcVar1[1] != '\0') {
    FUN_08007c40(param_1);
    FUN_0800802c(param_1,pcVar1[1]);
    pcVar1[1] = '\0';
  }
  if (*pcVar1 != '\0') {
    FUN_08007c40(param_1);
    FUN_0800802c(param_1,*pcVar1);
    *pcVar1 = '\0';
  }
  if (*(int *)(*(int *)(param_1 + 0x488) + 0x1c) != 0) {
    FUN_080002d8();
    *(undefined4 *)(*(int *)(param_1 + 0x488) + 0x1c) = 0;
  }
  return 0;
}



/* 08008850 */

undefined4 FUN_08008850(int param_1)

{
  undefined1 uVar1;
  byte bVar2;
  char cVar3;
  undefined1 uVar4;
  uint uVar5;
  int iVar6;
  undefined4 uVar7;
  int iVar8;
  ushort uVar9;
  undefined1 *puVar10;
  
  uVar5 = FUN_08007f30(param_1,*(undefined1 *)(*(int *)(param_1 + 0x488) + 4),0,0xff);
  if ((uVar5 < 2) && (iVar6 = FUN_08009460(param_1,uVar5), iVar6 == 0)) {
    iVar6 = FUN_080002ae(1,0x3c);
    *(int *)(*(int *)(param_1 + 0x488) + 0x1c) = iVar6;
    if (iVar6 != 0) {
      iVar8 = (short)uVar5 * 0x1a + param_1;
      cVar3 = *(char *)(iVar8 + 0x455);
      *(undefined4 *)(iVar6 + 4) = 7;
      if (cVar3 == '\x01') {
        puVar10 = &LAB_08008998_1;
      }
      else if (cVar3 == '\x02') {
        puVar10 = &LAB_080089e0_1;
      }
      else {
        if ((*(short *)(param_1 + 0x43c) != 0x575) && (*(short *)(param_1 + 0x43c) != 0x526)) {
          return 2;
        }
        if (*(short *)(param_1 + 0x43a) != 0x2563) {
          return 2;
        }
        puVar10 = &LAB_080086b0_1;
      }
      *(undefined4 *)(iVar6 + 4) = 0;
      *(undefined4 *)(iVar6 + 0xc) = 0;
      uVar1 = *(undefined1 *)(iVar8 + 0x45a);
      *(undefined1 **)(iVar6 + 0x38) = puVar10;
      bVar2 = *(byte *)(iVar8 + 0x45e);
      uVar9 = (ushort)bVar2;
      cVar3 = *(char *)(iVar8 + 0x452);
      *(undefined1 *)(iVar6 + 0x22) = uVar1;
      *(undefined2 *)(iVar6 + 0x20) = *(undefined2 *)(iVar8 + 0x45c);
      if (bVar2 < 0x33) {
        uVar9 = 0x32;
      }
      *(ushort *)(iVar6 + 0x24) = uVar9;
      if (cVar3 != '\0') {
        if (0x7fffffff < (uint)(int)*(char *)(iVar8 + 0x45a)) {
          *(char *)(iVar6 + 9) = *(char *)(iVar8 + 0x45a);
          uVar7 = FUN_08007b6c(param_1);
          uVar1 = *(undefined1 *)(param_1 + 0x429);
          uVar4 = *(undefined1 *)(param_1 + 0x428);
          *(char *)(iVar6 + 1) = (char)uVar7;
          FUN_08008f50(param_1,uVar7,*(undefined1 *)(iVar6 + 9),uVar4,uVar1,3,
                       *(undefined2 *)(iVar6 + 0x20));
          FUN_08008ec0(param_1,*(undefined1 *)(iVar6 + 1),0);
        }
        if ((cVar3 != '\x01') && (0x7fffffff < (uint)(int)*(char *)(iVar8 + 0x462))) {
          *(char *)(iVar6 + 9) = *(char *)(iVar8 + 0x462);
          uVar7 = FUN_08007b6c(param_1);
          uVar1 = *(undefined1 *)(param_1 + 0x429);
          uVar4 = *(undefined1 *)(param_1 + 0x428);
          *(char *)(iVar6 + 1) = (char)uVar7;
          FUN_08008f50(param_1,uVar7,*(undefined1 *)(iVar6 + 9),uVar4,uVar1,3,
                       *(undefined2 *)(iVar6 + 0x20));
          FUN_08008ec0(param_1,*(undefined1 *)(iVar6 + 1),0);
        }
      }
      return 0;
    }
  }
  return 2;
}



/* 08008a24 */

undefined4 FUN_08008a24(int param_1)

{
  uint uVar1;
  int iVar2;
  undefined4 uVar3;
  undefined4 uVar4;
  int iVar5;
  
  uVar4 = 0;
  iVar5 = *(int *)(*(int *)(param_1 + 0x488) + 0x1c);
  switch(*(undefined4 *)(iVar5 + 4)) {
  case 0:
    (**(code **)(iVar5 + 0x38))(param_1);
    *(undefined4 *)(iVar5 + 4) = 1;
    break;
  case 1:
    uVar1 = FUN_080087d8(param_1,1,0,*(undefined4 *)(iVar5 + 0x1c),*(undefined1 *)(iVar5 + 0x20));
    if (uVar1 < 4) {
      uVar3 = *(undefined4 *)(&DAT_08008b4c + uVar1 * 4);
      uVar4 = *(undefined4 *)(&DAT_08008b5c + uVar1 * 4);
    }
    else {
      uVar3 = 7;
      uVar4 = 2;
    }
    *(undefined4 *)(iVar5 + 4) = uVar3;
    goto LAB_08008b12;
  default:
    goto switchD_08008a38_caseD_2;
  case 4:
    FUN_08008ca8(param_1,*(undefined4 *)(iVar5 + 0x1c),*(undefined1 *)(iVar5 + 0x20),
                 *(undefined1 *)(iVar5 + 1));
    *(undefined4 *)(iVar5 + 4) = 6;
    *(undefined4 *)(iVar5 + 0x28) = *(undefined4 *)(param_1 + 0x4d0);
    *(undefined1 *)(iVar5 + 0x2c) = 0;
    return 0;
  case 5:
    if ((*(uint *)(param_1 + 0x4d0) & 1) != 0) {
      *(undefined4 *)(iVar5 + 4) = 4;
    }
LAB_08008b12:
    *(undefined4 *)(param_1 + 0x4ec) = 2;
    FUN_0800d4f0(*(undefined4 *)(param_1 + 0x4e4),param_1 + 0x4ec,0,0);
    return uVar4;
  case 6:
    iVar2 = FUN_08008d88(param_1,*(undefined1 *)(iVar5 + 1));
    if (iVar2 != 1) {
      iVar2 = FUN_08008d88(param_1,*(undefined1 *)(iVar5 + 1));
      if (iVar2 == 5) {
        iVar2 = FUN_08007c4c(param_1,*(undefined1 *)(iVar5 + 0x22));
        if (iVar2 == 0) {
          *(undefined4 *)(iVar5 + 4) = 4;
        }
      }
      return 0;
    }
    iVar2 = FUN_08008d6c(param_1);
    if (*(char *)(iVar5 + 0x2c) != '\0') {
      return 0;
    }
    if (iVar2 == 0) {
      return 0;
    }
    FUN_08008630(iVar5 + 0x10,*(undefined4 *)(iVar5 + 0x1c),*(undefined2 *)(iVar5 + 0x20));
    *(undefined1 *)(iVar5 + 0x2c) = 1;
    FUN_08008574(param_1);
  }
  *(undefined4 *)(param_1 + 0x4ec) = 2;
  FUN_0800d4f0(*(undefined4 *)(param_1 + 0x4e4),param_1 + 0x4ec,0,0);
switchD_08008a38_caseD_2:
  return 0;
}



/* 08008bb0 */

void FUN_08008bb0(int param_1,short param_2,ushort param_3)

{
  *(undefined2 *)(param_1 + 0x18) = 0xa21;
  *(ushort *)(param_1 + 0x1a) = param_3 | param_2 << 8;
  *(undefined4 *)(param_1 + 0x1c) = 0;
  FUN_08007c90(param_1,0,0);
  return;
}



/* 08008bc8 */

void FUN_08008bc8(int param_1,int param_2)

{
  *(undefined2 *)(param_1 + 0x18) = 0xb21;
  *(ushort *)(param_1 + 0x1a) = (ushort)(param_2 == 0);
  *(undefined4 *)(param_1 + 0x1c) = 0;
  FUN_08007c90(param_1,0,0);
  return;
}



/* 08008be4 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined4 FUN_08008be4(undefined4 *param_1,int param_2,undefined1 param_3)

{
  undefined4 uVar1;
  
  if (param_1 != (undefined4 *)0x0) {
    *(undefined1 *)(param_1 + 0x136) = param_3;
    FUN_08000788(param_1 + 0x122,0x48);
    *param_1 = 0;
    param_1[1] = 0;
    param_1[2] = 1;
    param_1[0x134] = 0;
    param_1[8] = 1;
    *(undefined1 *)((int)param_1 + 0xe) = 0x40;
    param_1[0x10a] = 0x100;
    *(undefined1 *)(param_1 + 9) = 0;
    FUN_08000788(param_1 + 10,0x400);
    FUN_08000744((int)param_1 + 0x432,0x50);
    *(undefined1 *)((int)param_1 + 0x42f) = 0;
    *(undefined1 *)(param_1 + 0x10b) = 0;
    *(undefined1 *)((int)param_1 + 0x42d) = 0;
    *(undefined1 *)((int)param_1 + 0x42e) = 0;
    if (param_2 != 0) {
      param_1[0x138] = param_2;
    }
    uVar1 = FUN_0800d45c(0x10,4,0);
    param_1[0x139] = uVar1;
    _DAT_2001c4f4 = s_USBH_Queue_08008c9c;
    _DAT_2001c508 = 0x800;
    _DAT_2001c50c = 0x18;
    uVar1 = FUN_0800d80c(&LAB_08009420_1,param_1);
    param_1[0x13a] = uVar1;
    FUN_08008db0(param_1);
    return 0;
  }
  return 2;
}



/* 08008ca8 */

undefined4 FUN_08008ca8(undefined4 param_1,undefined4 param_2,undefined4 param_3,undefined4 param_4)

{
  FUN_08008f1c(param_1,param_4,1,3,1,param_2,param_3,0);
  return 0;
}



/* 08008cd0 */

undefined4 FUN_08008cd0(int param_1)

{
  uint uVar1;
  undefined4 uVar2;
  
  uVar1 = FUN_08001fcc(*(undefined4 *)(param_1 + 0x4dc));
  if (uVar1 < 4) {
    uVar2 = *(undefined4 *)(&DAT_080134b0 + uVar1 * 4);
  }
  else {
    uVar2 = 2;
  }
  return uVar2;
}



/* 08008d60 */

undefined4 FUN_08008d60(void)

{
  FUN_08001db0(200);
  return 0;
}



/* 08008d6c */

undefined4 FUN_08008d6c(int param_1,int param_2)

{
  return *(undefined4 *)(*(int *)(param_1 + 0x4dc) + param_2 * 0x40 + 0x38);
}



/* 08008d74 */

uint FUN_08008d74(int param_1)

{
  uint uVar1;
  
  uVar1 = FUN_08001fb4(*(undefined4 *)(param_1 + 0x4dc));
  if (2 < uVar1) {
    uVar1 = 1;
  }
  return uVar1;
}



/* 08008d88 */

undefined4 FUN_08008d88(int param_1,int param_2)

{
  return *(undefined4 *)(*(int *)(param_1 + 0x4dc) + param_2 * 0x40 + 0x4c);
}



/* 08008db0 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined4 FUN_08008db0(int param_1)

{
  int iVar1;
  undefined4 uVar2;
  
  if (*(char *)(param_1 + 0x4d8) != '\0') {
    return 0;
  }
  _DAT_2001d66c = param_1;
  *(undefined1 **)(param_1 + 0x4dc) = &DAT_2001d24c;
  _DAT_2001d24c = 0x40040000;
  _DAT_2001d251 = 0xc;
  DAT_2001d253 = 1;
  _DAT_2001d255 = 2;
  DAT_2001d257 = 0;
  DAT_2001d25a = 0;
  DAT_2001d25c = 0;
  iVar1 = FUN_08002a9c(&DAT_2001d24c);
  if (iVar1 != 0) {
    FUN_08001414();
  }
  uVar2 = FUN_08001fac(&DAT_2001d24c);
  FUN_08008eb8(param_1,uVar2);
  return 0;
}



/* 08008e3c */

undefined4 FUN_08008e3c(int param_1)

{
  uint uVar1;
  undefined4 uVar2;
  
  uVar1 = FUN_08001ff4(*(undefined4 *)(param_1 + 0x4dc));
  if (uVar1 < 4) {
    uVar2 = *(undefined4 *)(&DAT_080134b0 + uVar1 * 4);
  }
  else {
    uVar2 = 2;
  }
  return uVar2;
}



/* 08008e98 */

undefined4 FUN_08008e98(int param_1)

{
  uint uVar1;
  undefined4 uVar2;
  
  uVar1 = FUN_08002bb0(*(undefined4 *)(param_1 + 0x4dc));
  if (uVar1 < 4) {
    uVar2 = *(undefined4 *)(&DAT_080134b0 + uVar1 * 4);
  }
  else {
    uVar2 = 2;
  }
  return uVar2;
}



/* 08008eb8 */

void FUN_08008eb8(int param_1,undefined4 param_2)

{
  *(undefined4 *)(param_1 + 0x4d0) = param_2;
  return;
}



/* 08008ec0 */

undefined4 FUN_08008ec0(int param_1,int param_2,undefined1 param_3)

{
  int iVar1;
  
  iVar1 = *(int *)(param_1 + 0x4dc) + param_2 * 0x40;
  if (*(char *)(iVar1 + 0x17) == '\0') {
    *(undefined1 *)(iVar1 + 0x3d) = param_3;
  }
  else {
    *(undefined1 *)(iVar1 + 0x3c) = param_3;
  }
  return 0;
}



/* 08008edc */

undefined4 FUN_08008edc(int param_1)

{
  uint uVar1;
  undefined4 uVar2;
  
  uVar1 = FUN_08002bc0(*(undefined4 *)(param_1 + 0x4dc));
  if (uVar1 < 4) {
    uVar2 = *(undefined4 *)(&DAT_080134b0 + uVar1 * 4);
  }
  else {
    uVar2 = 2;
  }
  return uVar2;
}



/* 08008efc */

undefined4 FUN_08008efc(int param_1)

{
  uint uVar1;
  undefined4 uVar2;
  
  uVar1 = FUN_08002bf0(*(undefined4 *)(param_1 + 0x4dc));
  if (uVar1 < 4) {
    uVar2 = *(undefined4 *)(&DAT_080134b0 + uVar1 * 4);
  }
  else {
    uVar2 = 2;
  }
  return uVar2;
}



/* 08008f1c */

undefined4 FUN_08008f1c(int param_1)

{
  uint uVar1;
  undefined4 uVar2;
  
  uVar1 = FUN_080020a0(*(undefined4 *)(param_1 + 0x4dc));
  if (uVar1 < 4) {
    uVar2 = *(undefined4 *)(&DAT_080134b0 + uVar1 * 4);
  }
  else {
    uVar2 = 2;
  }
  return uVar2;
}



/* 08008f50 */

undefined4 FUN_08008f50(void)

{
  FUN_08008e3c();
  return 0;
}



/* 08008f6c */

undefined4 FUN_08008f6c(undefined4 *param_1)

{
  char cVar1;
  bool bVar2;
  undefined1 uVar3;
  byte bVar4;
  int iVar5;
  undefined4 uVar6;
  undefined4 uVar7;
  
  if (*(char *)((int)param_1 + 0x42d) == '\x01') {
    *param_1 = 3;
  }
  switch(*param_1) {
  case 0:
    if (*(char *)(param_1 + 0x10b) == '\0') {
      return 0;
    }
    *param_1 = 1;
    thunk_FUN_08001db0(200);
    FUN_08008e98(param_1);
    *(undefined1 *)(param_1 + 0x10a) = 0;
    param_1[0x135] = 0;
    uVar7 = param_1[0x139];
    param_1[0x13b] = 1;
    goto LAB_08009252;
  case 1:
    if (*(char *)((int)param_1 + 0x42f) == '\x01') {
      *(undefined1 *)((int)param_1 + 0x42b) = 0;
      *param_1 = 2;
    }
    else if ((uint)param_1[0x135] < 0x3e9) {
      param_1[0x135] = param_1[0x135] + 10;
      thunk_FUN_08001db0(10);
    }
    else {
      cVar1 = *(char *)((int)param_1 + 0x42b);
      *(char *)((int)param_1 + 0x42b) = cVar1 + '\x01';
      if ((byte)(cVar1 + 1U) < 4) {
        uVar6 = 0;
      }
      else {
        uVar6 = 0xd;
      }
      *param_1 = uVar6;
    }
    break;
  case 2:
    if ((code *)param_1[0x138] != (code *)0x0) {
      (*(code *)param_1[0x138])(param_1,4);
    }
    thunk_FUN_08001db0(100);
    uVar3 = FUN_08008d74(param_1);
    *(undefined1 *)((int)param_1 + 0x429) = uVar3;
    *param_1 = 5;
    uVar3 = FUN_08007b6c(param_1,0);
    *(undefined1 *)((int)param_1 + 0xd) = uVar3;
    uVar6 = FUN_08007b6c(param_1,0x80);
    *(char *)(param_1 + 3) = (char)uVar6;
    FUN_08008f50(param_1,uVar6,0x80,*(undefined1 *)(param_1 + 0x10a),
                 *(undefined1 *)((int)param_1 + 0x429),0,*(undefined1 *)((int)param_1 + 0xe));
    FUN_08008f50(param_1,*(undefined1 *)((int)param_1 + 0xd),0,*(undefined1 *)(param_1 + 0x10a),
                 *(undefined1 *)((int)param_1 + 0x429),0,*(undefined1 *)((int)param_1 + 0xe));
    break;
  case 3:
    *(undefined1 *)((int)param_1 + 0x42d) = 0;
    FUN_08000788(param_1 + 0x124,0x40);
    *param_1 = 0;
    param_1[1] = 0;
    param_1[2] = 1;
    param_1[0x134] = 0;
    param_1[8] = 1;
    param_1[0x10a] = 0x100;
    *(undefined1 *)((int)param_1 + 0xe) = 0x40;
    *(undefined1 *)(param_1 + 9) = 0;
    FUN_08000788(param_1 + 10,0x400);
    FUN_08000744((int)param_1 + 0x432,0x50);
    if (param_1[0x122] != 0) {
      (**(code **)(param_1[0x122] + 0xc))(param_1);
      param_1[0x122] = 0;
    }
    if ((code *)param_1[0x138] != (code *)0x0) {
      (*(code *)param_1[0x138])(param_1,5);
    }
    if (*(char *)((int)param_1 + 0x42e) == '\x01') {
      *(undefined1 *)((int)param_1 + 0x42e) = 0;
      FUN_08008edc(param_1);
      FUN_08008d60(param_1,1);
    }
    else {
      FUN_08008edc(param_1);
    }
    break;
  default:
    goto switchD_08008f8a_caseD_4;
  case 5:
    switch(param_1[1]) {
    case 0:
      iVar5 = FUN_0800832c(param_1,8);
      if (iVar5 == 3) {
        bVar4 = *(char *)((int)param_1 + 0x42a) + 1;
        *(byte *)((int)param_1 + 0x42a) = bVar4;
        if (bVar4 < 4) {
          FUN_0800802c(param_1,*(undefined1 *)((int)param_1 + 0xd));
          FUN_0800802c(param_1,*(undefined1 *)(param_1 + 3));
          uVar6 = 0;
        }
        else {
LAB_080093d4:
          uVar6 = 0xd;
        }
LAB_080093d6:
        *param_1 = uVar6;
        break;
      }
      if (iVar5 != 0) break;
      bVar2 = true;
      *(undefined1 *)((int)param_1 + 0xe) = *(undefined1 *)((int)param_1 + 0x439);
      param_1[1] = 1;
      FUN_08008f50(param_1,*(undefined1 *)(param_1 + 3),0x80,*(undefined1 *)(param_1 + 0x10a),
                   *(undefined1 *)((int)param_1 + 0x429),0,*(undefined1 *)((int)param_1 + 0x439));
      FUN_08008f50(param_1,*(undefined1 *)((int)param_1 + 0xd),0,*(undefined1 *)(param_1 + 0x10a),
                   *(undefined1 *)((int)param_1 + 0x429),0,*(undefined1 *)((int)param_1 + 0xe));
      goto LAB_080093da;
    case 1:
      iVar5 = FUN_0800832c(param_1,0x12);
      if (iVar5 == 3) {
LAB_08009338:
        bVar4 = *(char *)((int)param_1 + 0x42a) + 1;
        *(byte *)((int)param_1 + 0x42a) = bVar4;
        if (3 < bVar4) goto LAB_080093d4;
        FUN_0800802c(param_1,*(undefined1 *)((int)param_1 + 0xd));
        FUN_0800802c(param_1,*(undefined1 *)(param_1 + 3));
        uVar6 = 0;
        param_1[1] = 0;
        goto LAB_080093d6;
      }
      if (iVar5 == 0) {
        uVar6 = 2;
        goto LAB_080093be;
      }
      break;
    case 2:
      bVar2 = true;
      iVar5 = FUN_08009474(param_1,1);
      if (iVar5 == 3) {
        *param_1 = 0xd;
        uVar6 = 0;
LAB_080093be:
        param_1[1] = uVar6;
        break;
      }
      if (iVar5 == 0) {
        thunk_FUN_08001db0(2);
        bVar2 = true;
        *(undefined1 *)(param_1 + 0x10a) = 1;
        param_1[1] = 3;
        FUN_08008f50(param_1,*(undefined1 *)(param_1 + 3),0x80,1,
                     *(undefined1 *)((int)param_1 + 0x429),0,*(undefined1 *)((int)param_1 + 0xe));
        FUN_08008f50(param_1,*(undefined1 *)((int)param_1 + 0xd),0,*(undefined1 *)(param_1 + 0x10a),
                     *(undefined1 *)((int)param_1 + 0x429),0,*(undefined1 *)((int)param_1 + 0xe));
      }
      goto LAB_080093da;
    case 3:
      iVar5 = FUN_0800808c(param_1,9);
      if (iVar5 == 3) goto LAB_08009338;
      if (iVar5 == 0) {
        uVar6 = 4;
        goto LAB_080093be;
      }
      break;
    case 4:
      iVar5 = FUN_0800808c(param_1,*(undefined2 *)((int)param_1 + 0x446));
      if (iVar5 == 3) goto LAB_08009338;
      if (iVar5 == 0) {
        uVar6 = 5;
        goto LAB_080093be;
      }
      break;
    case 5:
      if (((*(char *)(param_1 + 0x110) == '\0') ||
          (iVar5 = FUN_080083e8(param_1,*(char *)(param_1 + 0x110),param_1 + 0x8a,0xff), iVar5 == 3)
          ) || (iVar5 == 0)) {
        uVar6 = 6;
LAB_0800939a:
        param_1[1] = uVar6;
        param_1[0x13b] = 5;
        FUN_0800d4f0(param_1[0x139],param_1 + 0x13b,0,0);
      }
      break;
    case 6:
      if ((*(char *)((int)param_1 + 0x441) == '\0') ||
         (iVar5 = FUN_080083e8(param_1,*(char *)((int)param_1 + 0x441),param_1 + 0x8a,0xff),
         iVar5 == 3)) {
        uVar6 = 7;
        goto LAB_0800939a;
      }
      if (iVar5 == 0) {
        uVar6 = 7;
        goto LAB_080093be;
      }
      break;
    case 7:
      if (*(char *)((int)param_1 + 0x442) == '\0') {
        bVar2 = false;
      }
      else {
        iVar5 = FUN_080083e8(param_1,*(char *)((int)param_1 + 0x442),param_1 + 0x8a,0xff);
        bVar2 = iVar5 != 0 && iVar5 != 3;
      }
      goto LAB_080093da;
    }
    bVar2 = true;
LAB_080093da:
    if (bVar2) {
switchD_08008f8a_caseD_4:
      return 0;
    }
    *(undefined1 *)(param_1 + 0x10c) = 0;
    uVar6 = 7;
    if (*(char *)((int)param_1 + 0x443) == '\x01') {
      uVar6 = 8;
    }
    *param_1 = uVar6;
    param_1[0x13b] = 5;
    uVar7 = param_1[0x139];
    goto LAB_08009252;
  case 6:
    if (param_1[0x122] != 0) {
      iVar5 = (**(code **)(param_1[0x122] + 0x10))(param_1);
      if (iVar5 == 0) {
        uVar6 = 0xb;
        goto LAB_080091dc;
      }
      if (iVar5 != 2) goto LAB_080091de;
    }
LAB_080091da:
    uVar6 = 0xd;
    goto LAB_080091dc;
  case 7:
    if ((code *)param_1[0x138] == (code *)0x0) {
      return 0;
    }
    (*(code *)param_1[0x138])(param_1,1);
    uVar6 = 8;
LAB_080091dc:
    *param_1 = uVar6;
LAB_080091de:
    uVar6 = 5;
    goto LAB_0800924a;
  case 8:
    iVar5 = FUN_08009490(param_1,*(undefined1 *)((int)param_1 + 0x449));
    if (iVar5 == 0) {
      *param_1 = 9;
    }
    break;
  case 9:
    if (((-1 < (int)((uint)*(byte *)((int)param_1 + 1099) << 0x1a)) ||
        (iVar5 = FUN_080094ac(param_1,1), iVar5 == 0)) || (iVar5 == 3)) {
      *param_1 = 10;
    }
    break;
  case 10:
    if (param_1[0x123] != 0) {
      iVar5 = param_1[0x121];
      if (*(char *)(iVar5 + 4) != *(char *)((int)param_1 + 0x453)) {
        iVar5 = 0;
      }
      param_1[0x122] = iVar5;
      if ((iVar5 == 0) || (iVar5 = (**(code **)(iVar5 + 8))(param_1), iVar5 != 0))
      goto LAB_080091da;
      *param_1 = 6;
      (*(code *)param_1[0x138])(param_1,3);
    }
    goto LAB_080091de;
  case 0xb:
    if (param_1[0x122] != 0) {
      (**(code **)(param_1[0x122] + 0x14))(param_1);
      return 0;
    }
    goto switchD_08008f8a_caseD_4;
  }
  uVar6 = 1;
LAB_0800924a:
  uVar7 = param_1[0x139];
  param_1[0x13b] = uVar6;
LAB_08009252:
  FUN_0800d4f0(uVar7,param_1 + 0x13b,0,0);
  return 0;
}



/* 08009444 */

undefined4 FUN_08009444(int param_1,int param_2)

{
  if ((param_2 != 0) && (*(int *)(param_1 + 0x48c) == 0)) {
    *(undefined4 *)(param_1 + 0x48c) = 1;
    *(int *)(param_1 + 0x484) = param_2;
    return 0;
  }
  return 2;
}



/* 08009460 */

undefined4 FUN_08009460(int param_1,uint param_2)

{
  undefined4 uVar1;
  
  if (param_2 < *(byte *)(param_1 + 0x448)) {
    *(char *)(param_1 + 0x430) = (char)param_2;
    uVar1 = 0;
  }
  else {
    uVar1 = 2;
  }
  return uVar1;
}



/* 08009474 */

void FUN_08009474(int param_1,undefined2 param_2)

{
  if (*(int *)(param_1 + 8) == 1) {
    *(undefined2 *)(param_1 + 0x1a) = param_2;
    *(undefined2 *)(param_1 + 0x18) = 0x500;
    *(undefined4 *)(param_1 + 0x1c) = 0;
  }
  FUN_08007c90(param_1,0,0);
  return;
}



/* 08009490 */

void FUN_08009490(int param_1,undefined2 param_2)

{
  if (*(int *)(param_1 + 8) == 1) {
    *(undefined2 *)(param_1 + 0x1a) = param_2;
    *(undefined2 *)(param_1 + 0x18) = 0x900;
    *(undefined4 *)(param_1 + 0x1c) = 0;
  }
  FUN_08007c90(param_1,0,0);
  return;
}



/* 080094ac */

void FUN_080094ac(int param_1,undefined2 param_2)

{
  if (*(int *)(param_1 + 8) == 1) {
    *(undefined2 *)(param_1 + 0x1a) = param_2;
    *(undefined2 *)(param_1 + 0x18) = 0x300;
    *(undefined4 *)(param_1 + 0x1c) = 0;
  }
  FUN_08007c90(param_1,0,0);
  return;
}



/* 080094c8 */

undefined4 FUN_080094c8(undefined4 param_1)

{
  FUN_08008edc();
  FUN_08008d60(param_1,1);
  return 0;
}



/* 08009518 */

undefined4 FUN_08009518(int param_1,uint param_2,uint param_3,uint param_4,char param_5)

{
  uint uVar1;
  undefined4 uVar2;
  uint local_8;
  uint local_4;
  
  if ((param_3 & 0xff00) != 0x100) {
    *(uint *)(param_1 + 0xc) = *(uint *)(param_1 + 0xc) | 0x40;
    local_4 = 0;
    do {
      if (0xf000000 < local_4 + 1) goto LAB_080096f4;
      if (*(int *)(param_1 + 0x10) < 0) break;
      if (0xf000000 < local_4 + 2) goto LAB_080096f4;
      if (*(int *)(param_1 + 0x10) < 0) break;
      if (0xf000000 < local_4 + 3) goto LAB_080096f4;
      if (*(int *)(param_1 + 0x10) < 0) break;
      local_4 = local_4 + 4;
      if (0xf000000 < local_4) goto LAB_080096f4;
    } while (*(uint *)(param_1 + 0x10) < 0x80000000);
    local_4 = 0;
    *(uint *)(param_1 + 0x10) = *(uint *)(param_1 + 0x10) | 1;
    do {
      if (0xf000000 < local_4 + 1) goto LAB_080096f4;
      if ((*(uint *)(param_1 + 0x10) & 1) == 0) break;
      if (0xf000000 < local_4 + 2) goto LAB_080096f4;
      if ((*(uint *)(param_1 + 0x10) & 1) == 0) break;
      if (0xf000000 < local_4 + 3) goto LAB_080096f4;
      if ((*(uint *)(param_1 + 0x10) & 1) == 0) break;
      local_4 = local_4 + 4;
      if (0xf000000 < local_4) goto LAB_080096f4;
    } while ((*(uint *)(param_1 + 0x10) & 1) != 0);
    uVar2 = 0;
    goto LAB_080096f8;
  }
  *(uint *)(param_1 + 0x38) = *(uint *)(param_1 + 0x38) & 0xfffeffff;
  *(uint *)(param_1 + 0xc) = *(uint *)(param_1 + 0xc) & 0xffbdffbf;
  *(uint *)(param_1 + 0xc) = *(uint *)(param_1 + 0xc) & 0xffcfffff;
  if (param_5 == '\x01') {
    *(uint *)(param_1 + 0xc) = *(uint *)(param_1 + 0xc) | 0x100000;
  }
  local_8 = 0;
  do {
    if (0xf000000 < local_8 + 1) goto LAB_080096e4;
    if (*(int *)(param_1 + 0x10) < 0) break;
    if (0xf000000 < local_8 + 2) goto LAB_080096e4;
    if (*(int *)(param_1 + 0x10) < 0) break;
    if (0xf000000 < local_8 + 3) goto LAB_080096e4;
    if (*(int *)(param_1 + 0x10) < 0) break;
    local_8 = local_8 + 4;
    if (0xf000000 < local_8) goto LAB_080096e4;
  } while (*(uint *)(param_1 + 0x10) < 0x80000000);
  local_8 = 0;
  *(uint *)(param_1 + 0x10) = *(uint *)(param_1 + 0x10) | 1;
  do {
    if (0xf000000 < local_8 + 1) goto LAB_080096e4;
    if ((*(uint *)(param_1 + 0x10) & 1) == 0) break;
    if (0xf000000 < local_8 + 2) goto LAB_080096e4;
    if ((*(uint *)(param_1 + 0x10) & 1) == 0) break;
    if (0xf000000 < local_8 + 3) goto LAB_080096e4;
    if ((*(uint *)(param_1 + 0x10) & 1) == 0) break;
    local_8 = local_8 + 4;
    if (0xf000000 < local_8) goto LAB_080096e4;
  } while ((*(uint *)(param_1 + 0x10) & 1) != 0);
  uVar2 = 0;
  if ((param_2 & 0xff0000) != 0x10000) {
    return 0;
  }
  goto LAB_08009714;
LAB_080096f4:
  uVar2 = 3;
LAB_080096f8:
  if ((param_4 & 0xff00) == 0) {
    uVar1 = *(uint *)(param_1 + 0x38) | 0x10000;
  }
  else {
    uVar1 = *(uint *)(param_1 + 0x38) & 0xfffeffff;
  }
  *(uint *)(param_1 + 0x38) = uVar1;
  goto joined_r0x08009712;
LAB_080096e4:
  uVar2 = 3;
joined_r0x08009712:
  if ((param_2 & 0xff0000) == 0x10000) {
LAB_08009714:
    *(uint *)(param_1 + 8) = *(uint *)(param_1 + 8) | 6;
    *(uint *)(param_1 + 8) = *(uint *)(param_1 + 8) | 0x20;
  }
  return uVar2;
}



/* 0800972c */

undefined4 FUN_0800972c(int param_1)

{
  *(uint *)(param_1 + 8) = *(uint *)(param_1 + 8) & 0xfffffffe;
  return 0;
}



/* 0800973c */

undefined4 FUN_0800973c(int param_1,int param_2)

{
  uint uVar1;
  
  uVar1 = *(uint *)(param_1 + 0x440);
  if (param_2 != 1 || (uVar1 & 0x1000) != 0) {
    if ((param_2 == 0) && ((uVar1 & 0x1000) != 0)) {
      *(uint *)(param_1 + 0x440) = uVar1 & 0xffffefd1;
    }
    return 0;
  }
  *(uint *)(param_1 + 0x440) = uVar1 & 0xffffffd1 | 0x1000;
  return 0;
}



/* 08009788 */

undefined4 FUN_08009788(int param_1)

{
  *(uint *)(param_1 + 8) = *(uint *)(param_1 + 8) | 1;
  return 0;
}



/* 08009798 */

undefined4 FUN_08009798(int param_1)

{
  undefined4 local_4;
  
  local_4 = 0;
  do {
    if (0xf000000 < local_4 + 1) {
      return 3;
    }
    if (*(int *)(param_1 + 0x10) < 0) break;
    if (0xf000000 < local_4 + 2) {
      return 3;
    }
    if (*(int *)(param_1 + 0x10) < 0) break;
    if (0xf000000 < local_4 + 3) {
      return 3;
    }
    if (*(int *)(param_1 + 0x10) < 0) break;
    local_4 = local_4 + 4;
    if (0xf000000 < local_4) {
      return 3;
    }
  } while (*(uint *)(param_1 + 0x10) < 0x80000000);
  local_4 = 0;
  *(undefined4 *)(param_1 + 0x10) = 0x10;
  do {
    if (0xf000000 < local_4 + 1) {
      return 3;
    }
    if (-1 < *(int *)(param_1 + 0x10) << 0x1b) {
      return 0;
    }
    if (0xf000000 < local_4 + 2) {
      return 3;
    }
    if (-1 < *(int *)(param_1 + 0x10) << 0x1b) {
      return 0;
    }
    if (0xf000000 < local_4 + 3) {
      return 3;
    }
    if (-1 < *(int *)(param_1 + 0x10) << 0x1b) {
      return 0;
    }
    local_4 = local_4 + 4;
    if (0xf000000 < local_4) {
      return 3;
    }
  } while (*(int *)(param_1 + 0x10) << 0x1b < 0);
  return 0;
}



/* 08009858 */

undefined4 FUN_08009858(int param_1,int param_2)

{
  undefined4 local_4;
  
  local_4 = 0;
  do {
    if (0xf000000 < local_4 + 1) {
      return 3;
    }
    if (*(int *)(param_1 + 0x10) < 0) break;
    if (0xf000000 < local_4 + 2) {
      return 3;
    }
    if (*(int *)(param_1 + 0x10) < 0) break;
    if (0xf000000 < local_4 + 3) {
      return 3;
    }
    if (*(int *)(param_1 + 0x10) < 0) break;
    local_4 = local_4 + 4;
    if (0xf000000 < local_4) {
      return 3;
    }
  } while (*(uint *)(param_1 + 0x10) < 0x80000000);
  local_4 = 0;
  *(int *)(param_1 + 0x10) = param_2 * 0x40 + 0x20;
  do {
    if (0xf000000 < local_4 + 1) {
      return 3;
    }
    if (-1 < *(int *)(param_1 + 0x10) << 0x1a) {
      return 0;
    }
    if (0xf000000 < local_4 + 2) {
      return 3;
    }
    if (-1 < *(int *)(param_1 + 0x10) << 0x1a) {
      return 0;
    }
    if (0xf000000 < local_4 + 3) {
      return 3;
    }
    if (-1 < *(int *)(param_1 + 0x10) << 0x1a) {
      return 0;
    }
    local_4 = local_4 + 4;
    if (0xf000000 < local_4) {
      return 3;
    }
  } while (*(int *)(param_1 + 0x10) << 0x1a < 0);
  return 0;
}



/* 08009920 */

uint FUN_08009920(int param_1)

{
  return (*(uint *)(param_1 + 0x440) & 0x7ffff) >> 0x11;
}



/* 08009938 */

uint FUN_08009938(int param_1)

{
  return *(uint *)(param_1 + 0x14) & 1;
}



/* 08009940 */

undefined4 FUN_08009940(int param_1,int param_2)

{
  uint uVar1;
  int iVar2;
  uint *puVar3;
  uint local_c;
  
  local_c = 0;
  iVar2 = param_1 + param_2 * 0x20;
  puVar3 = (uint *)(iVar2 + 0x500);
  if ((*(int *)(param_1 + 8) << 0x1a < 0) && (-1 < *(int *)(iVar2 + 0x504))) {
    if (*(uint *)(iVar2 + 0x500) < 0x80000000) {
      return 0;
    }
    if ((*(uint *)(iVar2 + 0x500) & 0x40000) != 0) {
      return 0;
    }
  }
  else if ((int)(*(uint *)(iVar2 + 0x500) << 0xd) < 0) {
    *puVar3 = *puVar3 | 0x40000000;
    uVar1 = *puVar3;
    if ((*(uint *)(param_1 + 0x410) & 0xff0000) == 0) {
      *puVar3 = uVar1 & 0x7fffffff;
      *puVar3 = *puVar3 | 0x80000000;
      do {
        if (1000 < local_c + 1) {
          return 0;
        }
        if (*puVar3 < 0x80000000) {
          return 0;
        }
        if (1000 < local_c + 2) {
          return 0;
        }
        if (*puVar3 < 0x80000000) {
          return 0;
        }
        if (1000 < local_c + 3) {
          return 0;
        }
        if (*puVar3 < 0x80000000) {
          return 0;
        }
        local_c = local_c + 4;
        if (1000 < local_c) {
          return 0;
        }
      } while ((int)*puVar3 < 0);
      return 0;
    }
    goto LAB_08009ab4;
  }
  *puVar3 = *puVar3 | 0x40000000;
  if (*(int *)(param_1 + 8) << 0x1a < 0) {
    uVar1 = *puVar3;
  }
  else {
    uVar1 = *puVar3;
    if ((*(uint *)(param_1 + 0x2c) & 0xff0000) == 0) {
      *puVar3 = uVar1 & 0x7fffffff;
      *puVar3 = *puVar3 | 0x80000000;
      while( true ) {
        if (((1000 < local_c + 1) || (*puVar3 < 0x80000000)) || (1000 < local_c + 2)) {
          return 0;
        }
        if (*puVar3 < 0x80000000) {
          return 0;
        }
        if (1000 < local_c + 3) break;
        if (*puVar3 < 0x80000000) {
          return 0;
        }
        local_c = local_c + 4;
        if (1000 < local_c) {
          return 0;
        }
        if (-1 < (int)*puVar3) {
          return 0;
        }
      }
      return 0;
    }
  }
LAB_08009ab4:
  *puVar3 = uVar1 | 0x80000000;
  return 0;
}



/* 08009ac4 */

undefined4
FUN_08009ac4(int param_1,uint param_2,uint param_3,uint param_4,int param_5,uint param_6,
            uint param_7)

{
  char cVar1;
  int iVar2;
  uint uVar3;
  undefined4 uVar4;
  uint *puVar5;
  
  iVar2 = param_1 + param_2 * 0x20;
  puVar5 = (uint *)(iVar2 + 0x500);
  *(undefined4 *)(iVar2 + 0x508) = 0xffffffff;
  cVar1 = (char)param_3;
  switch(param_6) {
  case 0:
  case 2:
    *(undefined4 *)(iVar2 + 0x50c) = 0x49d;
    if (cVar1 < '\0') {
LAB_08009b3e:
      uVar3 = 0x100;
LAB_08009b42:
      *(uint *)(iVar2 + 0x50c) = *(uint *)(iVar2 + 0x50c) | uVar3;
    }
    else if (param_1 == 0x40040000) {
      uVar3 = 0x60;
      goto LAB_08009b42;
    }
    break;
  case 1:
    *(undefined4 *)(iVar2 + 0x50c) = 0x225;
    if (0x7fffffff < (uint)(int)cVar1) {
      uVar3 = 0x180;
      goto LAB_08009b42;
    }
    break;
  case 3:
    *(undefined4 *)(iVar2 + 0x50c) = 0x69d;
    if (0x7fffffff < (uint)(int)cVar1) goto LAB_08009b3e;
    break;
  default:
    uVar4 = 1;
    goto LAB_08009b4e;
  }
  uVar4 = 0;
LAB_08009b4e:
  *(undefined4 *)(iVar2 + 0x504) = 0;
  *(uint *)(iVar2 + 0x50c) = *(uint *)(iVar2 + 0x50c) | 2;
  *(uint *)(param_1 + 0x418) = 1 << (param_2 & 0xf) | *(uint *)(param_1 + 0x418);
  *(uint *)(param_1 + 0x18) = *(uint *)(param_1 + 0x18) | 0x2000000;
  iVar2 = 0x100000;
  if ((*(uint *)(param_1 + 0x440) & 0x60000) != 0x40000) {
    iVar2 = 0x120000;
  }
  if (param_5 != 2) {
    iVar2 = 0x100000;
  }
  *puVar5 = iVar2 + ((param_3 & 0x80) << 8 | (param_3 & 0xf) << 0xb | (param_4 & 0x7f) << 0x16 |
                    (param_6 & 3) << 0x12) + (param_7 & 0x7ff);
  if ((param_6 & 0xfd) == 1) {
    *puVar5 = *puVar5 | 0x20000000;
  }
  return uVar4;
}



/* 08009bec */

uint FUN_08009bec(int param_1)

{
  return *(uint *)(param_1 + 0x414) & 0xffff;
}



/* 08009bf4 */

undefined4 FUN_08009bf4(int param_1,int param_2,int param_3)

{
  undefined4 *puVar1;
  char cVar2;
  undefined4 *puVar3;
  byte bVar4;
  undefined4 uVar5;
  int iVar6;
  uint uVar7;
  uint uVar8;
  uint *puVar9;
  uint uVar10;
  int iVar11;
  char cVar12;
  uint uVar13;
  uint local_18;
  
  uVar13 = (uint)*(byte *)(param_2 + 1);
  if (param_1 == 0x40040000) {
    if (param_3 == 1) {
      if (((*(byte *)(param_2 + 0x12) | 2) == 2) && (*(char *)(param_2 + 6) == '\0')) {
        *(uint *)(uVar13 * 0x20 + 0x4004050c) = *(uint *)(uVar13 * 0x20 + 0x4004050c) & 0xffffff8f;
      }
    }
    else if ((*(char *)(param_2 + 4) == '\0') && (*(char *)(param_2 + 5) == '\x01')) {
      iVar11 = uVar13 * 0x20;
      *(undefined4 *)(iVar11 + 0x40040510) = 0x80080000;
      *(uint *)(iVar11 + 0x40040500) = *(uint *)(iVar11 + 0x40040500) & 0x3fffffff | 0x80000000;
      return 0;
    }
  }
  cVar2 = *(char *)(param_2 + 6);
  if (cVar2 == '\x01') {
    cVar12 = *(char *)(param_2 + 3);
    if (cVar12 == '\0') {
      if (*(char *)(param_2 + 0x12) == '\x01') {
        uVar7 = *(uint *)(param_2 + 0x20);
        if (uVar7 < 0xbd) {
          *(uint *)(param_2 + 0x1c) = uVar7;
          if (*(int *)(param_2 + 0xc) - 1U < 2) {
            uVar5 = 3;
          }
          else {
            uVar5 = 4;
          }
        }
        else {
          uVar7 = (uint)*(ushort *)(param_2 + 0x14);
          *(uint *)(param_2 + 0x1c) = uVar7;
          *(uint *)(param_2 + 0x20) = uVar7;
          if (1 < *(int *)(param_2 + 0xc) - 1U) {
            uVar10 = 1;
            *(undefined4 *)(param_2 + 0xc) = 1;
            goto LAB_08009d08;
          }
          uVar5 = 2;
        }
        *(undefined4 *)(param_2 + 0xc) = uVar5;
        uVar10 = 1;
      }
      else {
        uVar8 = *(uint *)(param_2 + 0x20);
        if ((param_3 == 1) && (uVar7 = (uint)*(ushort *)(param_2 + 0x14), uVar7 < uVar8)) {
          *(uint *)(param_2 + 0x1c) = uVar7;
          uVar10 = 1;
          cVar12 = '\0';
          goto LAB_08009d0a;
        }
        *(uint *)(param_2 + 0x1c) = uVar8;
        uVar10 = 1;
        uVar7 = uVar8;
      }
LAB_08009d08:
      cVar12 = '\0';
    }
    else {
      uVar7 = (uint)*(ushort *)(param_2 + 0x14);
      uVar10 = 1;
      *(uint *)(param_2 + 0x1c) = uVar7;
    }
  }
  else {
    uVar7 = *(uint *)(param_2 + 0x20);
    if (uVar7 == 0) {
      uVar10 = 1;
      cVar12 = *(char *)(param_2 + 3);
    }
    else {
      uVar10 = ((uVar7 + *(ushort *)(param_2 + 0x14)) - 1) / (uint)*(ushort *)(param_2 + 0x14);
      if (0x100 < (uVar10 & 0xffff)) {
        uVar10 = 0x100;
      }
      cVar12 = *(char *)(param_2 + 3);
    }
    if (cVar12 == '\0') {
      *(uint *)(param_2 + 0x1c) = uVar7;
      goto LAB_08009d08;
    }
    uVar7 = (uint)*(ushort *)(param_2 + 0x14) * (uVar10 & 0xffff);
    *(uint *)(param_2 + 0x1c) = uVar7;
  }
LAB_08009d0a:
  iVar11 = param_1 + uVar13 * 0x20;
  *(uint *)(iVar11 + 0x510) =
       uVar7 & 0x7ffff | (uVar10 & 0x3ff) << 0x13 | (*(byte *)(param_2 + 0x16) & 3) << 0x1d;
  puVar9 = (uint *)(iVar11 + 0x500);
  if (param_3 != 0) {
    *(undefined4 *)(iVar11 + 0x514) = *(undefined4 *)(param_2 + 0x18);
  }
  iVar6 = *(int *)(param_1 + 0x408);
  *puVar9 = *puVar9 & 0xdfffffff;
  *puVar9 = ~(iVar6 << 0x1d) & 0x20000000U | *puVar9;
  if (cVar2 == '\x01') {
    cVar2 = *(char *)(param_2 + 7);
    *(uint *)(iVar11 + 0x504) =
         ((uint)*(byte *)(param_2 + 0x10) | (uint)*(byte *)(param_2 + 0x11) << 7) + 0x80000000;
    *(uint *)(iVar11 + 0x50c) = *(uint *)(iVar11 + 0x50c) | 0x60;
    if (cVar2 == '\x01' && cVar12 == '\0') {
      *(uint *)(iVar11 + 0x504) = *(uint *)(iVar11 + 0x504) | 0x10000;
      *(uint *)(iVar11 + 0x50c) = *(uint *)(iVar11 + 0x50c) | 0x40;
      bVar4 = *(byte *)(param_2 + 0x12);
      if ((bVar4 | 2) == 3) goto LAB_08009dfa;
      goto LAB_08009d84;
    }
    bVar4 = *(byte *)(param_2 + 0x12);
    if ((bVar4 | 2) != 3) goto LAB_08009d84;
LAB_08009dfa:
    if (cVar2 == '\x01' && cVar12 == '\x01') {
      *(uint *)(iVar11 + 0x504) = *(uint *)(iVar11 + 0x504) | 0x10000;
LAB_08009e34:
      local_18 = *puVar9 & 0xbfffffff;
      goto LAB_08009e40;
    }
    if (bVar4 != 1) goto LAB_08009d84;
    if (cVar12 != '\0') goto LAB_08009e34;
    uVar7 = *(int *)(param_2 + 0xc) - 1;
    if (uVar7 < 4) {
      *(uint *)(iVar11 + 0x504) = *(uint *)(&DAT_08009edc + uVar7 * 4) | *(uint *)(iVar11 + 0x504);
    }
    local_18 = *puVar9 & 0xbfffffff;
  }
  else {
    *(undefined4 *)(iVar11 + 0x504) = 0;
LAB_08009d84:
    local_18 = *puVar9 & 0xbfffffff;
    if (cVar12 != '\0') {
LAB_08009e40:
      *puVar9 = local_18 | 0x80008000;
      return 0;
    }
  }
  *puVar9 = local_18 & 0xffff7fff | 0x80000000;
  if (param_3 != 0) {
    return 0;
  }
  uVar7 = *(uint *)(param_2 + 0x20);
  if (uVar7 == 0) {
    return 0;
  }
  if (*(char *)(param_2 + 7) != '\0') {
    return 0;
  }
  switch(*(undefined1 *)(param_2 + 0x12)) {
  case 0:
  case 2:
    if ((uVar7 + 3 & 0x3ffff) >> 2 <= (*(uint *)(param_1 + 0x2c) & 0xffff))
    goto switchD_08009dc4_default;
    uVar10 = 0x20;
    break;
  case 1:
  case 3:
    if ((uVar7 + 3 & 0x3ffff) >> 2 <= (*(uint *)(param_1 + 0x410) & 0xffff))
    goto switchD_08009dc4_default;
    uVar10 = 0x4000000;
    break;
  default:
    goto switchD_08009dc4_default;
  }
  *(uint *)(param_1 + 0x18) = uVar10 | *(uint *)(param_1 + 0x18);
switchD_08009dc4_default:
  if ((uVar7 & 0xffff) != 0) {
    uVar7 = (uVar7 & 0xffff) + 3;
    puVar3 = *(undefined4 **)(param_2 + 0x18);
    param_1 = param_1 + 0x1000;
    iVar11 = uVar13 * 0x1000;
    uVar13 = (uVar7 & 0xf) >> 2;
    if (2 < (uVar7 >> 2) - 1) {
      uVar7 = uVar7 >> 2 & 0xfffffffc;
      do {
        uVar7 = uVar7 - 4;
        *(undefined4 *)(iVar11 + param_1) = *puVar3;
        *(undefined4 *)(iVar11 + param_1) = puVar3[1];
        *(undefined4 *)(iVar11 + param_1) = puVar3[2];
        puVar1 = puVar3 + 3;
        puVar3 = puVar3 + 4;
        *(undefined4 *)(iVar11 + param_1) = *puVar1;
      } while (uVar7 != 0);
    }
    if ((uVar13 != 0) && (*(undefined4 *)(param_1 + iVar11) = *puVar3, uVar13 != 1)) {
      *(undefined4 *)(param_1 + iVar11) = puVar3[1];
      if (uVar13 != 2) {
        puVar3 = (undefined4 *)puVar3[2];
      }
      if (uVar13 != 2) {
        *(undefined4 **)(param_1 + iVar11) = puVar3;
      }
      return 0;
    }
  }
  return 0;
}



/* 08009eec */

undefined4 FUN_08009eec(int param_1,uint param_2)

{
  uint uVar1;
  undefined4 uVar2;
  int iVar3;
  int iVar4;
  uint uVar5;
  uint local_18;
  uint local_14;
  
  *(undefined4 *)(param_1 + 0xe00) = 0;
  *(uint *)(param_1 + 0x38) = *(uint *)(param_1 + 0x38) | 0x200000;
  *(uint *)(param_1 + 0x38) = *(uint *)(param_1 + 0x38) & 0xfff7ffff;
  *(uint *)(param_1 + 0x38) = *(uint *)(param_1 + 0x38) & 0xfffbffff;
  if (*(int *)(param_1 + 0xc) << 0x19 < 0) {
    uVar1 = *(uint *)(param_1 + 0x400);
LAB_08009f3c:
    uVar1 = uVar1 & 0xfffffffb;
  }
  else {
    uVar1 = *(uint *)(param_1 + 0x400);
    if ((param_2 & 0xff000000) != 0x1000000) goto LAB_08009f3c;
    uVar1 = uVar1 | 4;
  }
  *(uint *)(param_1 + 0x400) = uVar1;
  uVar1 = param_2 >> 8;
  local_18 = 0;
  do {
    if (0xf000000 < local_18 + 1) goto LAB_0800a00c;
    if (*(int *)(param_1 + 0x10) < 0) break;
    if (0xf000000 < local_18 + 2) goto LAB_0800a00c;
    if (*(int *)(param_1 + 0x10) < 0) break;
    if (0xf000000 < local_18 + 3) goto LAB_0800a00c;
    if (*(int *)(param_1 + 0x10) < 0) break;
    local_18 = local_18 + 4;
    if (0xf000000 < local_18) goto LAB_0800a00c;
  } while (*(uint *)(param_1 + 0x10) < 0x80000000);
  local_18 = 0;
  *(undefined4 *)(param_1 + 0x10) = 0x420;
  do {
    if (0xf000000 < local_18 + 1) goto LAB_0800a00c;
    if (-1 < *(int *)(param_1 + 0x10) << 0x1a) break;
    if (0xf000000 < local_18 + 2) goto LAB_0800a00c;
    if (-1 < *(int *)(param_1 + 0x10) << 0x1a) break;
    if (0xf000000 < local_18 + 3) goto LAB_0800a00c;
    if (-1 < *(int *)(param_1 + 0x10) << 0x1a) break;
    local_18 = local_18 + 4;
    if (0xf000000 < local_18) goto LAB_0800a00c;
  } while (*(int *)(param_1 + 0x10) << 0x1a < 0);
  uVar2 = 0;
  goto LAB_0800a00e;
LAB_0800a0d0:
  uVar2 = 1;
  goto joined_r0x0800a0d4;
LAB_0800a00c:
  uVar2 = 1;
LAB_0800a00e:
  local_14 = 0;
  do {
    if (0xf000000 < local_14 + 1) goto LAB_0800a0d0;
    if (*(int *)(param_1 + 0x10) < 0) break;
    if (0xf000000 < local_14 + 2) goto LAB_0800a0d0;
    if (*(int *)(param_1 + 0x10) < 0) break;
    if (0xf000000 < local_14 + 3) goto LAB_0800a0d0;
    if (*(int *)(param_1 + 0x10) < 0) break;
    local_14 = local_14 + 4;
    if (0xf000000 < local_14) goto LAB_0800a0d0;
  } while (*(uint *)(param_1 + 0x10) < 0x80000000);
  local_14 = 0;
  *(undefined4 *)(param_1 + 0x10) = 0x10;
  do {
    if (0xf000000 < local_14 + 1) goto LAB_0800a0d0;
    if (-1 < *(int *)(param_1 + 0x10) << 0x1b) break;
    if (0xf000000 < local_14 + 2) goto LAB_0800a0d0;
    if (-1 < *(int *)(param_1 + 0x10) << 0x1b) break;
    if (0xf000000 < local_14 + 3) {
      uVar2 = 1;
      break;
    }
    if (-1 < *(int *)(param_1 + 0x10) << 0x1b) break;
    local_14 = local_14 + 4;
    if (0xf000000 < local_14) goto LAB_0800a0d0;
  } while (*(int *)(param_1 + 0x10) << 0x1b < 0);
joined_r0x0800a0d4:
  if ((uVar1 & 0xff) != 0) {
    uVar5 = uVar1 & 3;
    iVar3 = 0;
    if (3 < (uVar1 & 0xff)) {
      iVar4 = param_1 + 0x560;
      do {
        iVar3 = iVar3 + 4;
        *(undefined4 *)(iVar4 + -0x58) = 0xffffffff;
        *(undefined4 *)(iVar4 + -0x54) = 0;
        *(undefined4 *)(iVar4 + -0x38) = 0xffffffff;
        *(undefined4 *)(iVar4 + -0x34) = 0;
        *(undefined4 *)(iVar4 + -0x18) = 0xffffffff;
        *(undefined4 *)(iVar4 + -0x14) = 0;
        *(undefined4 *)(iVar4 + 8) = 0xffffffff;
        *(undefined4 *)(iVar4 + 0xc) = 0;
        iVar4 = iVar4 + 0x80;
      } while ((uVar1 & 0xff) - uVar5 != iVar3);
    }
    if (uVar5 != 0) {
      iVar3 = param_1 + 0x500 + iVar3 * 0x20;
      *(undefined4 *)(iVar3 + 8) = 0xffffffff;
      *(undefined4 *)(iVar3 + 0xc) = 0;
      if (uVar5 != 1) {
        *(undefined4 *)(iVar3 + 0x28) = 0xffffffff;
        *(undefined4 *)(iVar3 + 0x2c) = 0;
        if (uVar5 != 2) {
          *(undefined4 *)(iVar3 + 0x48) = 0xffffffff;
          *(undefined4 *)(iVar3 + 0x4c) = 0;
        }
      }
    }
  }
  *(undefined4 *)(param_1 + 0x18) = 0;
  *(undefined4 *)(param_1 + 0x14) = 0xffffffff;
  if (param_1 == 0x40040000) {
    uRam40040024 = 0x200;
    uRam40040028 = 0x1000200;
    uRam40040100 = 0xe00300;
  }
  else {
    *(undefined4 *)(param_1 + 0x24) = 0x80;
    *(undefined4 *)(param_1 + 0x28) = 0x600080;
    *(undefined4 *)(param_1 + 0x100) = 0x4000e0;
  }
  if ((param_2 & 0xff0000) == 0) {
    *(uint *)(param_1 + 0x18) = *(uint *)(param_1 + 0x18) | 0x10;
  }
  *(uint *)(param_1 + 0x18) = *(uint *)(param_1 + 0x18) | 0xa3200008;
  return uVar2;
}



/* 0800a1cc */

undefined4 FUN_0800a1cc(int param_1,uint param_2)

{
  *(uint *)(param_1 + 0x400) = *(uint *)(param_1 + 0x400) & 0xfffffffc;
  *(uint *)(param_1 + 0x400) = *(uint *)(param_1 + 0x400) | param_2 & 3;
  if (param_2 == 1) {
    *(undefined4 *)(param_1 + 0x404) = 48000;
    return 0;
  }
  if (param_2 == 2) {
    *(undefined4 *)(param_1 + 0x404) = 6000;
    return 0;
  }
  return 1;
}



/* 0800a20c */

uint FUN_0800a20c(int param_1,int param_2)

{
  param_1 = param_1 + param_2 * 0x20;
  return *(uint *)(param_1 + 0x50c) & *(uint *)(param_1 + 0x508);
}



/* 0800a21c */

uint FUN_0800a21c(int param_1)

{
  return *(uint *)(param_1 + 0x18) & *(uint *)(param_1 + 0x14);
}



/* 0800a224 */

undefined4 * FUN_0800a224(int param_1,undefined4 *param_2,uint param_3)

{
  undefined4 uVar1;
  undefined4 *puVar2;
  uint uVar3;
  uint uVar4;
  
  uVar3 = param_3 >> 2;
  param_3 = param_3 & 3;
  puVar2 = param_2;
  if (uVar3 != 0) {
    uVar4 = uVar3 & 3;
    if (2 < uVar3 - 1) {
      uVar3 = uVar3 & 0xfffffffc;
      do {
        uVar3 = uVar3 - 4;
        *param_2 = *(undefined4 *)(param_1 + 0x1000);
        param_2[1] = *(undefined4 *)(param_1 + 0x1000);
        param_2[2] = *(undefined4 *)(param_1 + 0x1000);
        param_2[3] = *(undefined4 *)(param_1 + 0x1000);
        param_2 = param_2 + 4;
      } while (uVar3 != 0);
    }
    puVar2 = param_2;
    if (uVar4 != 0) {
      *param_2 = *(undefined4 *)(param_1 + 0x1000);
      puVar2 = param_2 + 1;
      if (uVar4 != 1) {
        param_2[1] = *(undefined4 *)(param_1 + 0x1000);
        if (uVar4 == 2) {
          puVar2 = param_2 + 2;
        }
        else {
          param_2[2] = *(undefined4 *)(param_1 + 0x1000);
          puVar2 = param_2 + 3;
        }
      }
    }
  }
  if (param_3 != 0) {
    uVar1 = *(undefined4 *)(param_1 + 0x1000);
    *(char *)puVar2 = (char)uVar1;
    if (param_3 == 1) {
      return (undefined4 *)((int)puVar2 + 1);
    }
    *(char *)((int)puVar2 + 1) = (char)((uint)uVar1 >> 8);
    if (param_3 == 2) {
      return (undefined4 *)((int)puVar2 + 2);
    }
    *(char *)((int)puVar2 + 2) = (char)((uint)uVar1 >> 0x10);
    puVar2 = (undefined4 *)((int)puVar2 + 3);
  }
  return puVar2;
}



/* 0800a310 */

bool FUN_0800a310(int param_1,int param_2)

{
  uint *puVar1;
  int iVar2;
  
  *(uint *)(param_1 + 0xc) = *(uint *)(param_1 + 0xc) & 0x9fffffff;
  if (param_2 == 0) {
    iVar2 = 10;
    *(uint *)(param_1 + 0xc) = *(uint *)(param_1 + 0xc) | 0x40000000;
    FUN_08001db0(10);
    puVar1 = (uint *)(param_1 + 0x14);
    if ((*puVar1 & 1) != 0) {
      FUN_08001db0(10);
      if ((*puVar1 & 1) != 0) {
        FUN_08001db0(10);
        if ((*puVar1 & 1) == 0) {
          return false;
        }
        FUN_08001db0(10);
        if ((*puVar1 & 1) == 0) {
          return false;
        }
        FUN_08001db0(10);
        if ((*puVar1 & 1) == 0) {
          return false;
        }
        FUN_08001db0(10);
        if ((*puVar1 & 1) == 0) {
          return false;
        }
        FUN_08001db0(10);
        if ((*puVar1 & 1) == 0) {
          return false;
        }
        FUN_08001db0(10);
        if ((*puVar1 & 1) == 0) {
          return false;
        }
        FUN_08001db0(10);
        if ((*puVar1 & 1) == 0) {
          return false;
        }
        FUN_08001db0(10);
        if ((*puVar1 & 1) == 0) {
          return false;
        }
        FUN_08001db0(10);
        if ((*puVar1 & 1) == 0) {
          return false;
        }
        FUN_08001db0(10);
        if ((*puVar1 & 1) == 0) {
          return false;
        }
        FUN_08001db0(10);
        if ((*puVar1 & 1) == 0) {
          return false;
        }
        FUN_08001db0(10);
        if ((*puVar1 & 1) == 0) {
          return false;
        }
        FUN_08001db0(10);
        if ((*puVar1 & 1) == 0) {
          return false;
        }
        FUN_08001db0(10);
        if ((*puVar1 & 1) == 0) {
          return false;
        }
        FUN_08001db0(10);
        if ((*puVar1 & 1) == 0) {
          return false;
        }
        FUN_08001db0(10);
        if ((*puVar1 & 1) == 0) {
          return false;
        }
        FUN_08001db0(10);
        if ((*puVar1 & 1) == 0) {
          return false;
        }
        goto LAB_0800a43e;
      }
      iVar2 = 0x14;
    }
  }
  else {
    if (param_2 != 1) {
      return true;
    }
    iVar2 = 10;
    *(uint *)(param_1 + 0xc) = *(uint *)(param_1 + 0xc) | 0x20000000;
    FUN_08001db0(10);
    puVar1 = (uint *)(param_1 + 0x14);
    if ((*puVar1 & 1) == 0) {
      FUN_08001db0(10);
      if ((*puVar1 & 1) != 0) {
        return false;
      }
      FUN_08001db0(10);
      if ((*puVar1 & 1) != 0) {
        return false;
      }
      FUN_08001db0(10);
      if ((*puVar1 & 1) != 0) {
        return false;
      }
      FUN_08001db0(10);
      if ((*puVar1 & 1) != 0) {
        return false;
      }
      FUN_08001db0(10);
      if ((*puVar1 & 1) != 0) {
        return false;
      }
      FUN_08001db0(10);
      if ((*puVar1 & 1) != 0) {
        return false;
      }
      FUN_08001db0(10);
      if ((*puVar1 & 1) != 0) {
        return false;
      }
      FUN_08001db0(10);
      if ((*puVar1 & 1) != 0) {
        return false;
      }
      FUN_08001db0(10);
      if ((*puVar1 & 1) != 0) {
        return false;
      }
      FUN_08001db0(10);
      if ((*puVar1 & 1) != 0) {
        return false;
      }
      FUN_08001db0(10);
      if ((*puVar1 & 1) != 0) {
        return false;
      }
      FUN_08001db0(10);
      if ((*puVar1 & 1) != 0) {
        return false;
      }
      FUN_08001db0(10);
      if ((*puVar1 & 1) != 0) {
        return false;
      }
      FUN_08001db0(10);
      if ((*puVar1 & 1) != 0) {
        return false;
      }
      FUN_08001db0(10);
      if ((*puVar1 & 1) != 0) {
        return false;
      }
      FUN_08001db0(10);
      if ((*puVar1 & 1) != 0) {
        return false;
      }
      FUN_08001db0(10);
      if ((*puVar1 & 1) != 0) {
        return false;
      }
      FUN_08001db0(10);
      if ((*puVar1 & 1) != 0) {
        return false;
      }
LAB_0800a43e:
      FUN_08001db0(10);
      return true;
    }
  }
  return iVar2 == 200;
}



/* 0800a678 */

undefined4 FUN_0800a678(int param_1)

{
  undefined4 uVar1;
  uint uVar2;
  uint local_c;
  uint local_8;
  uint local_4;
  
  local_c = 0;
  *(uint *)(param_1 + 8) = *(uint *)(param_1 + 8) & 0xfffffffe;
  local_8 = 0;
  do {
    if (0xf000000 < local_8 + 1) goto LAB_0800a73c;
    if (*(int *)(param_1 + 0x10) < 0) break;
    if (0xf000000 < local_8 + 2) goto LAB_0800a73c;
    if (*(int *)(param_1 + 0x10) < 0) break;
    if (0xf000000 < local_8 + 3) goto LAB_0800a73c;
    if (*(int *)(param_1 + 0x10) < 0) break;
    local_8 = local_8 + 4;
    if (0xf000000 < local_8) goto LAB_0800a73c;
  } while (*(uint *)(param_1 + 0x10) < 0x80000000);
  local_8 = 0;
  *(undefined4 *)(param_1 + 0x10) = 0x420;
  do {
    if (0xf000000 < local_8 + 1) goto LAB_0800a73c;
    if (-1 < *(int *)(param_1 + 0x10) << 0x1a) break;
    if (0xf000000 < local_8 + 2) goto LAB_0800a73c;
    if (-1 < *(int *)(param_1 + 0x10) << 0x1a) break;
    if (0xf000000 < local_8 + 3) goto LAB_0800a73c;
    if (-1 < *(int *)(param_1 + 0x10) << 0x1a) break;
    local_8 = local_8 + 4;
    if (0xf000000 < local_8) goto LAB_0800a73c;
  } while (*(int *)(param_1 + 0x10) << 0x1a < 0);
  uVar1 = 0;
LAB_0800a73e:
  local_4 = 0;
  do {
    if (0xf000000 < local_4 + 1) goto LAB_0800a7f0;
    if (*(int *)(param_1 + 0x10) < 0) break;
    if (0xf000000 < local_4 + 2) goto LAB_0800a7f0;
    if (*(int *)(param_1 + 0x10) < 0) break;
    if (0xf000000 < local_4 + 3) goto LAB_0800a7f0;
    if (*(int *)(param_1 + 0x10) < 0) break;
    local_4 = local_4 + 4;
    if (0xf000000 < local_4) goto LAB_0800a7f0;
  } while (*(uint *)(param_1 + 0x10) < 0x80000000);
  local_4 = 0;
  *(undefined4 *)(param_1 + 0x10) = 0x10;
  do {
    if (0xf000000 < local_4 + 1) goto LAB_0800a7f0;
    if (-1 < *(int *)(param_1 + 0x10) << 0x1b) break;
    if (0xf000000 < local_4 + 2) goto LAB_0800a7f0;
    if (-1 < *(int *)(param_1 + 0x10) << 0x1b) break;
    if (0xf000000 < local_4 + 3) goto LAB_0800a7f0;
    if (-1 < *(int *)(param_1 + 0x10) << 0x1b) break;
    local_4 = local_4 + 4;
    if (0xf000000 < local_4) goto LAB_0800a7f0;
  } while (*(int *)(param_1 + 0x10) << 0x1b < 0);
LAB_0800a7f2:
  *(uint *)(param_1 + 0x500) = (*(uint *)(param_1 + 0x500) & 0x3fff7fff) + 0x40000000;
  *(uint *)(param_1 + 0x520) = (*(uint *)(param_1 + 0x520) & 0x3fff7fff) + 0x40000000;
  *(uint *)(param_1 + 0x540) = (*(uint *)(param_1 + 0x540) & 0x3fff7fff) + 0x40000000;
  *(uint *)(param_1 + 0x560) = (*(uint *)(param_1 + 0x560) & 0x3fff7fff) + 0x40000000;
  *(uint *)(param_1 + 0x580) = (*(uint *)(param_1 + 0x580) & 0x3fff7fff) + 0x40000000;
  *(uint *)(param_1 + 0x5a0) = (*(uint *)(param_1 + 0x5a0) & 0x3fff7fff) + 0x40000000;
  *(uint *)(param_1 + 0x5c0) = (*(uint *)(param_1 + 0x5c0) & 0x3fff7fff) + 0x40000000;
  *(uint *)(param_1 + 0x5e0) = (*(uint *)(param_1 + 0x5e0) & 0x3fff7fff) + 0x40000000;
  *(uint *)(param_1 + 0x600) = (*(uint *)(param_1 + 0x600) & 0x3fff7fff) + 0x40000000;
  *(uint *)(param_1 + 0x620) = (*(uint *)(param_1 + 0x620) & 0x3fff7fff) + 0x40000000;
  *(uint *)(param_1 + 0x640) = (*(uint *)(param_1 + 0x640) & 0x3fff7fff) + 0x40000000;
  *(uint *)(param_1 + 0x660) = (*(uint *)(param_1 + 0x660) & 0x3fff7fff) + 0x40000000;
  *(uint *)(param_1 + 0x680) = (*(uint *)(param_1 + 0x680) & 0x3fff7fff) + 0x40000000;
  *(uint *)(param_1 + 0x6a0) = (*(uint *)(param_1 + 0x6a0) & 0x3fff7fff) + 0x40000000;
  *(uint *)(param_1 + 0x6c0) = (*(uint *)(param_1 + 0x6c0) & 0x3fff7fff) + 0x40000000;
  *(uint *)(param_1 + 0x6e0) = (*(uint *)(param_1 + 0x6e0) & 0x3fff7fff) + 0x40000000;
  *(uint *)(param_1 + 0x500) = (*(uint *)(param_1 + 0x500) & 0x3fff7fff) + 0xc0000000;
  while ((((uVar2 = local_c + 1, uVar2 < 0x3e9 && (0x7fffffff < *(uint *)(param_1 + 0x500))) &&
          (uVar2 = local_c + 2, uVar2 < 0x3e9)) &&
         ((0x7fffffff < *(uint *)(param_1 + 0x500) && (uVar2 = local_c + 3, uVar2 < 0x3e9))))) {
    if ((*(uint *)(param_1 + 0x500) < 0x80000000) ||
       ((local_c = local_c + 4, uVar2 = local_c, 1000 < local_c || (-1 < *(int *)(param_1 + 0x500)))
       )) break;
  }
  local_c = uVar2;
  *(uint *)(param_1 + 0x520) = (*(uint *)(param_1 + 0x520) & 0x3fff7fff) + 0xc0000000;
  while (((uVar2 = local_c + 1, uVar2 < 0x3e9 && (0x7fffffff < *(uint *)(param_1 + 0x520))) &&
         (uVar2 = local_c + 2, uVar2 < 0x3e9))) {
    if (((*(uint *)(param_1 + 0x520) < 0x80000000) || (uVar2 = local_c + 3, 1000 < uVar2)) ||
       ((*(uint *)(param_1 + 0x520) < 0x80000000 ||
        ((local_c = local_c + 4, uVar2 = local_c, 1000 < local_c || (-1 < *(int *)(param_1 + 0x520))
         ))))) break;
  }
  local_c = uVar2;
  *(uint *)(param_1 + 0x540) = (*(uint *)(param_1 + 0x540) & 0x3fff7fff) + 0xc0000000;
  while ((((uVar2 = local_c + 1, uVar2 < 0x3e9 && (0x7fffffff < *(uint *)(param_1 + 0x540))) &&
          (uVar2 = local_c + 2, uVar2 < 0x3e9)) &&
         ((0x7fffffff < *(uint *)(param_1 + 0x540) && (uVar2 = local_c + 3, uVar2 < 0x3e9))))) {
    if ((*(uint *)(param_1 + 0x540) < 0x80000000) ||
       ((local_c = local_c + 4, uVar2 = local_c, 1000 < local_c || (-1 < *(int *)(param_1 + 0x540)))
       )) break;
  }
  local_c = uVar2;
  *(uint *)(param_1 + 0x560) = (*(uint *)(param_1 + 0x560) & 0x3fff7fff) + 0xc0000000;
  while ((((uVar2 = local_c + 1, uVar2 < 0x3e9 && (0x7fffffff < *(uint *)(param_1 + 0x560))) &&
          (uVar2 = local_c + 2, uVar2 < 0x3e9)) &&
         ((0x7fffffff < *(uint *)(param_1 + 0x560) && (uVar2 = local_c + 3, uVar2 < 0x3e9))))) {
    if ((*(uint *)(param_1 + 0x560) < 0x80000000) ||
       ((local_c = local_c + 4, uVar2 = local_c, 1000 < local_c || (-1 < *(int *)(param_1 + 0x560)))
       )) break;
  }
  local_c = uVar2;
  *(uint *)(param_1 + 0x580) = (*(uint *)(param_1 + 0x580) & 0x3fff7fff) + 0xc0000000;
  while (((uVar2 = local_c + 1, uVar2 < 0x3e9 && (0x7fffffff < *(uint *)(param_1 + 0x580))) &&
         (uVar2 = local_c + 2, uVar2 < 0x3e9))) {
    if (((*(uint *)(param_1 + 0x580) < 0x80000000) || (uVar2 = local_c + 3, 1000 < uVar2)) ||
       ((*(uint *)(param_1 + 0x580) < 0x80000000 ||
        ((local_c = local_c + 4, uVar2 = local_c, 1000 < local_c || (-1 < *(int *)(param_1 + 0x580))
         ))))) break;
  }
  local_c = uVar2;
  *(uint *)(param_1 + 0x5a0) = (*(uint *)(param_1 + 0x5a0) & 0x3fff7fff) + 0xc0000000;
  while (((uVar2 = local_c + 1, uVar2 < 0x3e9 && (0x7fffffff < *(uint *)(param_1 + 0x5a0))) &&
         (uVar2 = local_c + 2, uVar2 < 0x3e9))) {
    if (((*(uint *)(param_1 + 0x5a0) < 0x80000000) || (uVar2 = local_c + 3, 1000 < uVar2)) ||
       ((*(uint *)(param_1 + 0x5a0) < 0x80000000 ||
        ((local_c = local_c + 4, uVar2 = local_c, 1000 < local_c || (-1 < *(int *)(param_1 + 0x5a0))
         ))))) break;
  }
  local_c = uVar2;
  *(uint *)(param_1 + 0x5c0) = (*(uint *)(param_1 + 0x5c0) & 0x3fff7fff) + 0xc0000000;
  while (((((uVar2 = local_c + 1, uVar2 < 0x3e9 && (0x7fffffff < *(uint *)(param_1 + 0x5c0))) &&
           (uVar2 = local_c + 2, uVar2 < 0x3e9)) &&
          ((0x7fffffff < *(uint *)(param_1 + 0x5c0) && (uVar2 = local_c + 3, uVar2 < 0x3e9)))) &&
         (0x7fffffff < *(uint *)(param_1 + 0x5c0)))) {
    local_c = local_c + 4;
    uVar2 = local_c;
    if ((1000 < local_c) || (-1 < *(int *)(param_1 + 0x5c0))) break;
  }
  local_c = uVar2;
  *(uint *)(param_1 + 0x5e0) = (*(uint *)(param_1 + 0x5e0) & 0x3fff7fff) + 0xc0000000;
  while (((uVar2 = local_c + 1, uVar2 < 0x3e9 && (0x7fffffff < *(uint *)(param_1 + 0x5e0))) &&
         (uVar2 = local_c + 2, uVar2 < 0x3e9))) {
    if (((*(uint *)(param_1 + 0x5e0) < 0x80000000) || (uVar2 = local_c + 3, 1000 < uVar2)) ||
       ((*(uint *)(param_1 + 0x5e0) < 0x80000000 ||
        ((local_c = local_c + 4, uVar2 = local_c, 1000 < local_c || (-1 < *(int *)(param_1 + 0x5e0))
         ))))) break;
  }
  local_c = uVar2;
  *(uint *)(param_1 + 0x600) = (*(uint *)(param_1 + 0x600) & 0x3fff7fff) + 0xc0000000;
  while ((((uVar2 = local_c + 1, uVar2 < 0x3e9 && (0x7fffffff < *(uint *)(param_1 + 0x600))) &&
          (uVar2 = local_c + 2, uVar2 < 0x3e9)) &&
         ((0x7fffffff < *(uint *)(param_1 + 0x600) && (uVar2 = local_c + 3, uVar2 < 0x3e9))))) {
    if ((*(uint *)(param_1 + 0x600) < 0x80000000) ||
       ((local_c = local_c + 4, uVar2 = local_c, 1000 < local_c || (-1 < *(int *)(param_1 + 0x600)))
       )) break;
  }
  local_c = uVar2;
  *(uint *)(param_1 + 0x620) = (*(uint *)(param_1 + 0x620) & 0x3fff7fff) + 0xc0000000;
  while ((((uVar2 = local_c + 1, uVar2 < 0x3e9 && (0x7fffffff < *(uint *)(param_1 + 0x620))) &&
          (uVar2 = local_c + 2, uVar2 < 0x3e9)) &&
         ((0x7fffffff < *(uint *)(param_1 + 0x620) && (uVar2 = local_c + 3, uVar2 < 0x3e9))))) {
    if ((*(uint *)(param_1 + 0x620) < 0x80000000) ||
       ((local_c = local_c + 4, uVar2 = local_c, 1000 < local_c || (-1 < *(int *)(param_1 + 0x620)))
       )) break;
  }
  local_c = uVar2;
  *(uint *)(param_1 + 0x640) = (*(uint *)(param_1 + 0x640) & 0x3fff7fff) + 0xc0000000;
  while (((uVar2 = local_c + 1, uVar2 < 0x3e9 && (0x7fffffff < *(uint *)(param_1 + 0x640))) &&
         (uVar2 = local_c + 2, uVar2 < 0x3e9))) {
    if (((*(uint *)(param_1 + 0x640) < 0x80000000) || (uVar2 = local_c + 3, 1000 < uVar2)) ||
       ((*(uint *)(param_1 + 0x640) < 0x80000000 ||
        ((local_c = local_c + 4, uVar2 = local_c, 1000 < local_c || (-1 < *(int *)(param_1 + 0x640))
         ))))) break;
  }
  local_c = uVar2;
  *(uint *)(param_1 + 0x660) = (*(uint *)(param_1 + 0x660) & 0x3fff7fff) + 0xc0000000;
  while (((uVar2 = local_c + 1, uVar2 < 0x3e9 && (0x7fffffff < *(uint *)(param_1 + 0x660))) &&
         (uVar2 = local_c + 2, uVar2 < 0x3e9))) {
    if (((*(uint *)(param_1 + 0x660) < 0x80000000) || (uVar2 = local_c + 3, 1000 < uVar2)) ||
       ((*(uint *)(param_1 + 0x660) < 0x80000000 ||
        ((local_c = local_c + 4, uVar2 = local_c, 1000 < local_c || (-1 < *(int *)(param_1 + 0x660))
         ))))) break;
  }
  local_c = uVar2;
  *(uint *)(param_1 + 0x680) = (*(uint *)(param_1 + 0x680) & 0x3fff7fff) + 0xc0000000;
  while ((((uVar2 = local_c + 1, uVar2 < 0x3e9 && (0x7fffffff < *(uint *)(param_1 + 0x680))) &&
          (uVar2 = local_c + 2, uVar2 < 0x3e9)) &&
         ((0x7fffffff < *(uint *)(param_1 + 0x680) && (uVar2 = local_c + 3, uVar2 < 0x3e9))))) {
    if ((*(uint *)(param_1 + 0x680) < 0x80000000) ||
       ((local_c = local_c + 4, uVar2 = local_c, 1000 < local_c || (-1 < *(int *)(param_1 + 0x680)))
       )) break;
  }
  local_c = uVar2;
  *(uint *)(param_1 + 0x6a0) = (*(uint *)(param_1 + 0x6a0) & 0x3fff7fff) + 0xc0000000;
  while (((uVar2 = local_c + 1, uVar2 < 0x3e9 && (0x7fffffff < *(uint *)(param_1 + 0x6a0))) &&
         (uVar2 = local_c + 2, uVar2 < 0x3e9))) {
    if (((*(uint *)(param_1 + 0x6a0) < 0x80000000) || (uVar2 = local_c + 3, 1000 < uVar2)) ||
       ((*(uint *)(param_1 + 0x6a0) < 0x80000000 ||
        ((local_c = local_c + 4, uVar2 = local_c, 1000 < local_c || (-1 < *(int *)(param_1 + 0x6a0))
         ))))) break;
  }
  local_c = uVar2;
  *(uint *)(param_1 + 0x6c0) = (*(uint *)(param_1 + 0x6c0) & 0x3fff7fff) + 0xc0000000;
  while ((((uVar2 = local_c + 1, uVar2 < 0x3e9 && (0x7fffffff < *(uint *)(param_1 + 0x6c0))) &&
          (uVar2 = local_c + 2, uVar2 < 0x3e9)) &&
         ((0x7fffffff < *(uint *)(param_1 + 0x6c0) && (uVar2 = local_c + 3, uVar2 < 0x3e9))))) {
    if ((*(uint *)(param_1 + 0x6c0) < 0x80000000) ||
       ((local_c = local_c + 4, uVar2 = local_c, 1000 < local_c || (-1 < *(int *)(param_1 + 0x6c0)))
       )) break;
  }
  local_c = uVar2;
  *(uint *)(param_1 + 0x6e0) = (*(uint *)(param_1 + 0x6e0) & 0x3fff7fff) + 0xc0000000;
  while (((((local_c + 1 < 0x3e9 && (0x7fffffff < *(uint *)(param_1 + 0x6e0))) &&
           (local_c + 2 < 0x3e9)) &&
          ((0x7fffffff < *(uint *)(param_1 + 0x6e0) && (local_c + 3 < 0x3e9)))) &&
         (0x7fffffff < *(uint *)(param_1 + 0x6e0)))) {
    local_c = local_c + 4;
    if ((1000 < local_c) || (-1 < *(int *)(param_1 + 0x6e0))) break;
  }
  *(undefined4 *)(param_1 + 0x414) = 0xffffffff;
  *(undefined4 *)(param_1 + 0x14) = 0xffffffff;
  *(uint *)(param_1 + 8) = *(uint *)(param_1 + 8) | 1;
  return uVar1;
LAB_0800a73c:
  uVar1 = 1;
  goto LAB_0800a73e;
LAB_0800a7f0:
  uVar1 = 1;
  goto LAB_0800a7f2;
}



/* 0800afb0 */

void UsageFault_Handler(void)

{
  do {
                    /* WARNING: Do nothing block with infinite loop */
  } while( true );
}



/* 0800afd4 */

undefined4
FUN_0800afd4(undefined1 *param_1,uint param_2,byte param_3,char param_4,int param_5,int param_6)

{
  int iVar1;
  undefined4 *puVar2;
  uint uVar3;
  byte local_25;
  
  local_25 = 0;
  iVar1 = (**(code **)(**(int **)(param_1 + 4) + 4))(*(int **)(param_1 + 4),*param_1,8,&local_25,1);
  uVar3 = (uint)(iVar1 != -1) & (local_25 & 2) >> 1;
  param_1[0x15] = (char)uVar3;
  if (uVar3 == 1) {
    param_1[0x15] = 0;
    local_25 = 0;
    iVar1 = (**(code **)(**(int **)(param_1 + 4) + 4))
                      (*(int **)(param_1 + 4),*param_1,8,&local_25,1);
    if (iVar1 != -1) {
      local_25 = local_25 & 0xfd;
      (**(code **)**(undefined4 **)(param_1 + 4))
                (*(undefined4 **)(param_1 + 4),*param_1,8,&local_25,1);
    }
  }
  local_25 = 0;
  iVar1 = (**(code **)(**(int **)(param_1 + 4) + 4))(*(int **)(param_1 + 4),*param_1,4,&local_25,1);
  if (iVar1 == -1) {
    return 0xffffffff;
  }
  local_25 = local_25 & 0x8f | (byte)(param_2 << 4);
  iVar1 = (**(code **)**(undefined4 **)(param_1 + 4))
                    (*(undefined4 **)(param_1 + 4),*param_1,4,&local_25,1);
  if (iVar1 != 0) {
    return 0xffffffff;
  }
  if (param_2 < 7) {
    *(undefined4 *)(param_1 + 0x10) = *(undefined4 *)(&DAT_0800b260 + param_2 * 4);
  }
  local_25 = 0;
  iVar1 = (**(code **)(**(int **)(param_1 + 4) + 4))(*(int **)(param_1 + 4),*param_1,4,&local_25,1);
  if (iVar1 == -1) {
    return 0xffffffff;
  }
  local_25 = local_25 & 0xf0 | param_3;
  iVar1 = (**(code **)**(undefined4 **)(param_1 + 4))
                    (*(undefined4 **)(param_1 + 4),*param_1,4,&local_25,1);
  if (iVar1 != 0) {
    return 0xffffffff;
  }
  if (param_5 == 0) {
    local_25 = 0;
    iVar1 = (**(code **)(**(int **)(param_1 + 4) + 4))
                      (*(int **)(param_1 + 4),*param_1,6,&local_25,1);
    if (iVar1 != -1) {
      puVar2 = *(undefined4 **)(param_1 + 4);
      local_25 = local_25 & 0xef;
      goto LAB_0800b14c;
    }
  }
  else {
    local_25 = 0;
    iVar1 = (**(code **)(**(int **)(param_1 + 4) + 4))
                      (*(int **)(param_1 + 4),*param_1,6,&local_25,1);
    if (iVar1 != -1) {
      puVar2 = *(undefined4 **)(param_1 + 4);
      local_25 = local_25 | 0x10;
LAB_0800b14c:
      (**(code **)*puVar2)(puVar2,*param_1,6,&local_25,1);
    }
  }
  local_25 = 0;
  iVar1 = (**(code **)(**(int **)(param_1 + 4) + 4))(*(int **)(param_1 + 4),*param_1,6,&local_25,1);
  if (iVar1 == -1) {
    return 0xffffffff;
  }
  local_25 = local_25 & 0x9f | param_4 << 5;
  iVar1 = (**(code **)**(undefined4 **)(param_1 + 4))
                    (*(undefined4 **)(param_1 + 4),*param_1,6,&local_25,1);
  if (iVar1 != 0) {
    return 0xffffffff;
  }
  if (param_6 == 0) {
    local_25 = 0;
    iVar1 = (**(code **)(**(int **)(param_1 + 4) + 4))
                      (*(int **)(param_1 + 4),*param_1,4,&local_25,1);
    if (iVar1 == -1) goto LAB_0800b210;
    puVar2 = *(undefined4 **)(param_1 + 4);
    local_25 = local_25 & 0x7f;
  }
  else {
    local_25 = 0;
    iVar1 = (**(code **)(**(int **)(param_1 + 4) + 4))
                      (*(int **)(param_1 + 4),*param_1,4,&local_25,1);
    if (iVar1 == -1) goto LAB_0800b210;
    puVar2 = *(undefined4 **)(param_1 + 4);
    local_25 = local_25 | 0x80;
  }
  (**(code **)*puVar2)(puVar2,*param_1,4,&local_25,1);
LAB_0800b210:
  if (uVar3 != 0) {
    param_1[0x15] = 1;
    local_25 = 0;
    iVar1 = (**(code **)(**(int **)(param_1 + 4) + 4))
                      (*(int **)(param_1 + 4),*param_1,8,&local_25,1);
    if (iVar1 != -1) {
      local_25 = local_25 | 2;
      (**(code **)**(undefined4 **)(param_1 + 4))
                (*(undefined4 **)(param_1 + 4),*param_1,8,&local_25,1);
    }
  }
  return 0;
}



/* 0800b27c */

undefined4
FUN_0800b27c(undefined1 *param_1,uint param_2,byte param_3,char param_4,int param_5,int param_6)

{
  int iVar1;
  undefined4 *puVar2;
  byte bVar3;
  byte local_25;
  
  local_25 = 0;
  iVar1 = (**(code **)(**(int **)(param_1 + 4) + 4))(*(int **)(param_1 + 4),*param_1,8,&local_25,1);
  bVar3 = iVar1 != -1 & local_25;
  param_1[0x14] = bVar3;
  if (bVar3 == 1) {
    param_1[0x14] = 0;
    local_25 = 0;
    iVar1 = (**(code **)(**(int **)(param_1 + 4) + 4))
                      (*(int **)(param_1 + 4),*param_1,8,&local_25,1);
    if (iVar1 != -1) {
      local_25 = local_25 & 0xfe;
      (**(code **)**(undefined4 **)(param_1 + 4))
                (*(undefined4 **)(param_1 + 4),*param_1,8,&local_25,1);
    }
  }
  local_25 = 0;
  iVar1 = (**(code **)(**(int **)(param_1 + 4) + 4))(*(int **)(param_1 + 4),*param_1,3,&local_25,1);
  if (iVar1 == -1) {
    return 0xffffffff;
  }
  local_25 = local_25 & 0x8f | (byte)(param_2 << 4);
  iVar1 = (**(code **)**(undefined4 **)(param_1 + 4))
                    (*(undefined4 **)(param_1 + 4),*param_1,3,&local_25,1);
  if (iVar1 != 0) {
    return 0xffffffff;
  }
  if (param_2 < 4) {
    *(undefined4 *)(param_1 + 0xc) = *(undefined4 *)(&DAT_0800b504 + param_2 * 4);
  }
  local_25 = 0;
  iVar1 = (**(code **)(**(int **)(param_1 + 4) + 4))(*(int **)(param_1 + 4),*param_1,3,&local_25,1);
  if (iVar1 == -1) {
    return 0xffffffff;
  }
  local_25 = local_25 & 0xf0 | param_3;
  iVar1 = (**(code **)**(undefined4 **)(param_1 + 4))
                    (*(undefined4 **)(param_1 + 4),*param_1,3,&local_25,1);
  if (iVar1 != 0) {
    return 0xffffffff;
  }
  if (param_5 == 0) {
    local_25 = 0;
    iVar1 = (**(code **)(**(int **)(param_1 + 4) + 4))
                      (*(int **)(param_1 + 4),*param_1,6,&local_25,1);
    if (iVar1 != -1) {
      puVar2 = *(undefined4 **)(param_1 + 4);
      local_25 = local_25 & 0xfe;
      goto LAB_0800b3f0;
    }
  }
  else {
    local_25 = 0;
    iVar1 = (**(code **)(**(int **)(param_1 + 4) + 4))
                      (*(int **)(param_1 + 4),*param_1,6,&local_25,1);
    if (iVar1 != -1) {
      puVar2 = *(undefined4 **)(param_1 + 4);
      local_25 = local_25 | 1;
LAB_0800b3f0:
      (**(code **)*puVar2)(puVar2,*param_1,6,&local_25,1);
    }
  }
  local_25 = 0;
  iVar1 = (**(code **)(**(int **)(param_1 + 4) + 4))(*(int **)(param_1 + 4),*param_1,6,&local_25,1);
  if (iVar1 == -1) {
    return 0xffffffff;
  }
  local_25 = local_25 & 0xf9 | param_4 << 1;
  iVar1 = (**(code **)**(undefined4 **)(param_1 + 4))
                    (*(undefined4 **)(param_1 + 4),*param_1,6,&local_25,1);
  if (iVar1 != 0) {
    return 0xffffffff;
  }
  if (param_6 == 0) {
    local_25 = 0;
    iVar1 = (**(code **)(**(int **)(param_1 + 4) + 4))
                      (*(int **)(param_1 + 4),*param_1,3,&local_25,1);
    if (iVar1 == -1) goto LAB_0800b4b4;
    puVar2 = *(undefined4 **)(param_1 + 4);
    local_25 = local_25 & 0x7f;
  }
  else {
    local_25 = 0;
    iVar1 = (**(code **)(**(int **)(param_1 + 4) + 4))
                      (*(int **)(param_1 + 4),*param_1,3,&local_25,1);
    if (iVar1 == -1) goto LAB_0800b4b4;
    puVar2 = *(undefined4 **)(param_1 + 4);
    local_25 = local_25 | 0x80;
  }
  (**(code **)*puVar2)(puVar2,*param_1,3,&local_25,1);
LAB_0800b4b4:
  if (bVar3 != 0) {
    param_1[0x14] = 1;
    local_25 = 0;
    iVar1 = (**(code **)(**(int **)(param_1 + 4) + 4))
                      (*(int **)(param_1 + 4),*param_1,8,&local_25,1);
    if (iVar1 != -1) {
      local_25 = local_25 | 1;
      (**(code **)**(undefined4 **)(param_1 + 4))
                (*(undefined4 **)(param_1 + 4),*param_1,8,&local_25,1);
    }
  }
  return 0;
}



/* 0800b514 */

undefined4 FUN_0800b514(undefined1 *param_1,int param_2,uint param_3)

{
  undefined1 uVar1;
  undefined1 *puVar2;
  int iVar3;
  int iVar4;
  undefined4 *puVar5;
  code *pcVar6;
  undefined1 local_26;
  char local_25;
  byte local_24;
  byte local_23;
  byte local_22;
  byte local_21;
  
  local_26 = 0xb0;
  (**(code **)**(undefined4 **)(param_1 + 4))
            (*(undefined4 **)(param_1 + 4),*param_1,0x60,&local_26,1);
  if (param_2 == 0) {
    local_22 = 0;
    iVar3 = (**(code **)(**(int **)(param_1 + 4) + 4))
                      (*(int **)(param_1 + 4),*param_1,2,&local_22,1);
    if (iVar3 == -1) {
      return 1;
    }
    puVar5 = *(undefined4 **)(param_1 + 4);
    local_21 = local_22 | 0x40;
    uVar1 = *param_1;
    pcVar6 = *(code **)*puVar5;
    puVar2 = &stack0xffffffef;
  }
  else {
    iVar3 = FUN_0800d358();
    iVar4 = FUN_0800d358();
    if (param_3 <= (uint)(iVar4 - iVar3)) {
      return 0;
    }
    while( true ) {
      local_25 = '\0';
      iVar4 = (**(code **)(**(int **)(param_1 + 4) + 4))
                        (*(int **)(param_1 + 4),*param_1,0x4d,&local_25,1);
      if ((iVar4 != -1) && (local_25 == -0x80)) break;
      FUN_0800d310(10);
      iVar4 = FUN_0800d358();
      if (param_3 <= (uint)(iVar4 - iVar3)) {
        return 0;
      }
    }
    local_24 = 0;
    iVar3 = (**(code **)(**(int **)(param_1 + 4) + 4))
                      (*(int **)(param_1 + 4),*param_1,2,&local_24,1);
    if (iVar3 == -1) {
      return 1;
    }
    puVar5 = *(undefined4 **)(param_1 + 4);
    local_23 = local_24 | 0x40;
    uVar1 = *param_1;
    pcVar6 = *(code **)*puVar5;
    puVar2 = &stack0xffffffed;
  }
  (*pcVar6)(puVar5,uVar1,2,puVar2 + -0x10,1);
  return 1;
}



/* 0800b61c */

undefined4 FUN_0800b61c(int param_1)

{
  undefined4 uVar1;
  
  uVar1 = 0;
  if (param_1 - 0x8004U < 0xfffffffd) {
    uVar1 = 0xffffffff;
  }
  return uVar1;
}



/* 0800b630 */

void FUN_0800b630(void)

{
  do {
                    /* WARNING: Do nothing block with infinite loop */
  } while( true );
}



/* 0800b634 */

undefined4 FUN_0800b634(void)

{
  return 0;
}



/* 0800b638 */

bool FUN_0800b638(int param_1)

{
  return param_1 - 0x8001U < 3;
}



/* 0800b648 */

undefined4 FUN_0800b648(char *param_1)

{
  int iVar1;
  undefined4 uVar2;
  
  if ((param_1 == (char *)0x0) || (*param_1 != ':')) {
    return 0xffffffff;
  }
  iVar1 = FUN_080007d8(param_1,s__STDIN_08013300);
  if (iVar1 == 0) {
    return 0x8001;
  }
  iVar1 = FUN_080007d8(param_1,s__STDOUT_08013307);
  if (iVar1 != 0) {
    iVar1 = FUN_080007d8(param_1,s__STDERR_080132f8);
    uVar2 = 0xffffffff;
    if (iVar1 == 0) {
      uVar2 = 0x8003;
    }
    return uVar2;
  }
  return 0x8002;
}



/* 0800b6a8 */

undefined4 FUN_0800b6a8(void)

{
  return 0xffffffff;
}



/* 0800b6b0 */

undefined4 FUN_0800b6b0(int param_1,int param_2,int param_3)

{
  undefined1 *puVar1;
  
  if (param_1 == 0x8003) {
    if (param_3 != 0) {
      puVar1 = (undefined1 *)(param_2 + -1);
      do {
        puVar1 = puVar1 + 1;
        FUN_0800fd3c(*puVar1);
        param_3 = param_3 + -1;
      } while (param_3 != 0);
    }
  }
  else {
    if (param_1 != 0x8002) {
      return 0xffffffff;
    }
    if (param_3 != 0) {
      puVar1 = (undefined1 *)(param_2 + -1);
      do {
        puVar1 = puVar1 + 1;
        FUN_0800fd54(*puVar1);
        param_3 = param_3 + -1;
      } while (param_3 != 0);
    }
  }
  return 0;
}



/* 0800b6f4 */

void thunk_FUN_0800fd6c(void)

{
  return;
}



/* 0800ba30 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_0800ba30(undefined4 *param_1,int param_2)

{
  undefined1 local_a;
  undefined1 local_9;
  
  local_a = (undefined1)*param_1;
  local_9 = (undefined1)param_2;
  FUN_0800e274(0x2001e468,6,&local_a,2);
  if (param_2 == 0x20) {
    FUN_0800bce0(_DAT_2001c3f0,2000,0x32,0x32,1);
  }
  return;
}



/* 0800bad8 */

void FUN_0800bad8(int param_1,int param_2)

{
  int iVar1;
  uint uVar2;
  int iVar3;
  undefined4 uVar4;
  code *pcVar5;
  undefined4 uVar6;
  
  *(int *)(param_1 + 0x14) = *(int *)(param_1 + 0x14) + param_2;
  iVar1 = (**(code **)(param_1 + 0x28))(param_1);
  if (iVar1 != *(int *)(param_1 + 8)) {
    *(int *)(param_1 + 8) = iVar1;
    return;
  }
  iVar3 = *(int *)(param_1 + 4);
  if ((*(int *)(param_1 + 0xc) == iVar1) && (1 < iVar3 - 1U)) {
    return;
  }
  *(int *)(param_1 + 0xc) = iVar1;
  if (iVar3 == 2) {
    if (iVar1 == 0) {
      (**(code **)(param_1 + 0x24))(param_1,8);
      *(undefined4 *)(param_1 + 0x10) = 0;
      *(int *)(param_1 + 0x14) = *(int *)(param_1 + 0x18) + 1;
      *(undefined4 *)(param_1 + 4) = 0;
      return;
    }
    if (*(uint *)(param_1 + 0x14) <= *(uint *)(param_1 + 0x20)) {
      return;
    }
    (**(code **)(param_1 + 0x24))(param_1,4);
    *(undefined4 *)(param_1 + 0x14) = 0;
    return;
  }
  if (iVar3 == 1) {
    if (iVar1 == 0) {
      (**(code **)(param_1 + 0x24))(param_1,0x10);
      (**(code **)(param_1 + 0x24))(param_1,0x20);
      uVar2 = *(uint *)(param_1 + 0x10);
      if (uVar2 < 2) {
        uVar2 = 1;
      }
      *(uint *)(param_1 + 0x10) = uVar2;
      *(undefined4 *)(param_1 + 4) = 0;
      return;
    }
    if (*(uint *)(param_1 + 0x14) <= *(uint *)(param_1 + 0x1c)) {
      return;
    }
    pcVar5 = *(code **)(param_1 + 0x24);
    uVar4 = 2;
    uVar6 = 2;
  }
  else {
    if (iVar3 != 0) {
      return;
    }
    if (iVar1 == 0) {
      if (*(uint *)(param_1 + 0x14) <= *(uint *)(param_1 + 0x18)) {
        return;
      }
      if (*(int *)(param_1 + 0x10) == 0) {
        return;
      }
      *(undefined4 *)(param_1 + 0x10) = 0;
      *(undefined4 *)(param_1 + 0x14) = 0;
      return;
    }
    uVar6 = 1;
    (**(code **)(param_1 + 0x24))(param_1,1);
    if ((*(uint *)(param_1 + 0x18) <= *(uint *)(param_1 + 0x14)) || (*(int *)(param_1 + 0x10) == 0))
    goto LAB_0800bb60;
    iVar1 = *(int *)(param_1 + 0x10) + 1;
    *(int *)(param_1 + 0x10) = iVar1;
    if (iVar1 == 2) {
      (**(code **)(param_1 + 0x24))(param_1,0x40);
      iVar1 = *(int *)(param_1 + 0x10);
    }
    if (iVar1 != 3) goto LAB_0800bb60;
    pcVar5 = *(code **)(param_1 + 0x24);
    uVar4 = 0x80;
  }
  (*pcVar5)(param_1,uVar4);
LAB_0800bb60:
  *(undefined4 *)(param_1 + 0x14) = 0;
  *(undefined4 *)(param_1 + 4) = uVar6;
  return;
}



/* 0800bce0 */

void FUN_0800bce0(int param_1,undefined2 param_2,undefined4 param_3,undefined4 param_4,
                 undefined2 param_5)

{
  undefined2 local_18 [2];
  undefined4 local_14;
  undefined4 uStack_10;
  undefined2 local_c;
  
  local_c = param_5;
  local_18[0] = param_2;
  local_14 = param_3;
  uStack_10 = param_4;
  (**(code **)(param_1 + 0x20))(param_1,local_18);
  return;
}



/* 0800bd00 */

void FUN_0800bd00(int param_1)

{
  *(undefined4 *)(param_1 + 4) = 3;
  return;
}



/* 0800bdb8 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_0800bdb8(void)

{
  undefined4 *puVar1;
  int iVar2;
  undefined4 local_28;
  undefined4 local_24;
  undefined4 uStack_20;
  undefined4 uStack_1c;
  undefined4 uStack_18;
  undefined4 local_14;
  
  FUN_08001f84(0x40020000,0x100,0);
  local_28 = DAT_0800be60;
  local_24 = DAT_0800be64;
  uStack_20 = DAT_0800be68;
  uStack_1c = DAT_0800be6c;
  uStack_18 = DAT_0800be70;
  local_14 = DAT_0800be74;
  _DAT_2001c3ec = FUN_0800d45c(5,0x10,&local_28);
  _DAT_2001c3f0 = (undefined4 *)FUN_0800c7cc(0,0x2001c084,0x28);
  FUN_0800bd00();
  puVar1 = _DAT_2001c3f0;
  _DAT_2001c3f0[7] = &LAB_0800c060_1;
  puVar1[8] = &LAB_0800ee80_1;
  *puVar1 = 1;
  iVar2 = _DAT_2001d97c;
  puVar1[9] = &LAB_0800bc64_1;
  *(undefined4 *)(iVar2 + 0x24) = 0;
  *(undefined4 *)(iVar2 + 0x10) = 0xfffffffe;
  *(undefined4 *)(iVar2 + 0x10) = 0xfffffffd;
  *(uint *)(iVar2 + 0xc) = *(uint *)(iVar2 + 0xc) | 1;
  *(uint *)(iVar2 + 0xc) = *(uint *)(iVar2 + 0xc) | 2;
  return;
}



/* 0800be78 */

uint FUN_0800be78(byte *param_1,uint param_2)

{
  byte *pbVar1;
  uint uVar2;
  uint uVar3;
  ushort uVar4;
  uint uVar5;
  
  if (param_2 != 0) {
    uVar5 = param_2 & 3;
    if (param_2 < 4) {
      uVar2 = 0;
    }
    else {
      uVar2 = 0;
      uVar4 = 0;
      pbVar1 = param_1;
      do {
        param_1 = pbVar1 + 4;
        uVar4 = uVar4 + 4;
        uVar2 = (uint)(byte)(&DAT_080133b0)
                            [(&DAT_080133b0)
                             [(&DAT_080133b0)[(&DAT_080133b0)[uVar2 ^ *pbVar1] ^ pbVar1[1]] ^
                              pbVar1[2]] ^ pbVar1[3]];
        pbVar1 = param_1;
      } while ((uint)uVar4 != (param_2 & 0xfffffffc));
    }
    if (uVar5 != 0) {
      uVar3 = uVar2 ^ *param_1;
      uVar2 = (uint)(byte)(&DAT_080133b0)[uVar3];
      if (uVar5 != 1) {
        uVar2 = (uint)(byte)(&DAT_080133b0)[(&DAT_080133b0)[uVar3] ^ param_1[1]];
        if (uVar5 != 2) {
          uVar2 = (uint)(byte)(&DAT_080133b0)
                              [param_1[2] ^ (&DAT_080133b0)[(&DAT_080133b0)[uVar3] ^ param_1[1]]];
        }
      }
    }
    return uVar2;
  }
  return 0;
}



/* 0800befc */

void FUN_0800befc(undefined4 param_1,int param_2)

{
  float fVar1;
  int iVar2;
  uint in_fpscr;
  float fVar3;
  float fVar4;
  
  iVar2 = FUN_08001f78(0x40020c00,8);
  fVar1 = DAT_0800bf9c;
  fVar3 = DAT_0800bf9c;
  if (iVar2 == 0) {
    FUN_0800e3a4(*(undefined4 *)(param_2 + 0x18),param_1,param_2 + 0x20);
    fVar3 = (float)VectorSignedToFloat(*(undefined4 *)(param_2 + 0x1c),(byte)(in_fpscr >> 0x16) & 3)
    ;
    fVar3 = *(float *)(param_2 + 0x38) + fVar3;
    if (DAT_0800bfa0 < fVar3) {
      fVar3 = DAT_0800bfa0;
    }
    if (fVar3 < DAT_0800bfa4) {
      fVar3 = DAT_0800bfa4;
    }
  }
  fVar4 = fVar3;
  if (ABS(fVar3) < DAT_0800bfa8) {
    fVar4 = fVar1;
  }
  (**(code **)(param_2 + 0x44))(param_2,(int)fVar4);
  *(int *)(param_2 + 0x1c) = (int)fVar3;
  return;
}



/* 0800bfe0 */

void FUN_0800bfe0(float param_1,int *param_2,undefined4 param_3,uint param_4,int param_5)

{
  longlong lVar1;
  uint uVar2;
  int iVar3;
  uint uVar4;
  uint in_fpscr;
  float fVar5;
  float fVar6;
  float fVar7;
  
  fVar7 = DAT_0800c048;
  uVar2 = param_2[4];
  lVar1 = (ulonglong)(uint)param_2[2] * (ulonglong)uVar2;
  uVar4 = (uint)lVar1;
  iVar3 = param_4 + uVar4;
  fVar5 = (float)VectorSignedToFloat(iVar3 - *param_2,(byte)(in_fpscr >> 0x16) & 3);
  fVar6 = (float)param_2[5] * DAT_0800c044;
  *param_2 = iVar3;
  param_2[1] = param_2[3] * uVar2 +
               param_2[2] * ((int)uVar2 >> 0x1f) + (int)((ulonglong)lVar1 >> 0x20) + param_5 +
               (uint)CARRY4(param_4,uVar4);
  fVar6 = (fVar5 / param_1) * fVar7 + fVar6;
  fVar7 = (float)VectorSignedToFloat(param_2[0xf],(byte)(in_fpscr >> 0x16) & 3);
  param_2[5] = (int)fVar6;
  param_2[6] = (int)(fVar6 / fVar7);
  return;
}



/* 0800c358 */

void FUN_0800c358(int param_1,undefined4 param_2,undefined4 param_3,undefined2 param_4)

{
  undefined4 local_14;
  undefined4 uStack_10;
  undefined2 local_c;
  
  local_14 = param_2;
  uStack_10 = param_3;
  local_c = param_4;
  (**(code **)(param_1 + 0x1c))(param_1,&local_14);
  return;
}



/* 0800c370 */

void FUN_0800c370(int param_1)

{
  *(undefined4 *)(param_1 + 4) = 3;
  return;
}



/* 0800c434 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_0800c434(void)

{
  undefined4 *puVar1;
  undefined4 local_20;
  undefined4 local_1c;
  undefined4 uStack_18;
  undefined4 uStack_14;
  undefined4 uStack_10;
  undefined4 local_c;
  
  local_20 = DAT_0800c4a4;
  local_1c = DAT_0800c4a8;
  uStack_18 = DAT_0800c4ac;
  uStack_14 = DAT_0800c4b0;
  uStack_10 = DAT_0800c4b4;
  local_c = DAT_0800c4b8;
  _DAT_2001c3e4 = FUN_0800d45c(5,0xc,&local_20);
  _DAT_2001c3e8 = (undefined4 *)FUN_0800c7cc(0,0x2001c084,0x24);
  FUN_0800c370();
  puVar1 = _DAT_2001c3e8;
  *_DAT_2001c3e8 = 1;
  puVar1[6] = &LAB_0800c04c_1;
  puVar1[7] = &LAB_0800ee6c_1;
  puVar1[8] = &LAB_0800c378_1;
  return;
}



/* 0800c4d0 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_0800c4d0(void)

{
  undefined4 local_28 [8];
  
  local_28[0] = 5;
  FUN_0800d4f0(_DAT_2001c234,local_28,0,10);
  return;
}



/* 0800c4f0 */

undefined4 FUN_0800c4f0(undefined4 *param_1,uint *param_2)

{
  undefined4 *puVar1;
  uint uVar2;
  int iVar3;
  undefined4 *puVar4;
  uint uVar5;
  uint uVar6;
  undefined4 *puVar7;
  uint uVar8;
  undefined4 *puVar9;
  uint uVar10;
  
  puVar7 = (undefined4 *)0x2001e3d0;
  if (param_1 != (undefined4 *)0x0) {
    puVar7 = param_1;
  }
  if ((param_2 != (uint *)0x0) && (puVar7[2] == 0)) {
    uVar2 = *param_2;
    uVar5 = param_2[1];
    if (uVar5 == 0 && uVar2 == 0) {
      uVar10 = 0;
    }
    else {
      uVar10 = 0;
      uVar6 = 0;
      uVar8 = 0;
      do {
        if (uVar2 < uVar6 + uVar8) {
          return 0;
        }
        uVar6 = param_2[uVar10 * 2 + 2];
        if (param_2[uVar10 * 2 + 3] == 0 && uVar6 == 0) {
          uVar10 = uVar10 + 1;
          break;
        }
        if (uVar6 < uVar2 + uVar5) {
          return 0;
        }
        uVar2 = param_2[uVar10 * 2 + 4];
        if (param_2[uVar10 * 2 + 5] == 0 && uVar2 == 0) {
          uVar10 = uVar10 + 2;
          break;
        }
        if (uVar2 < param_2[uVar10 * 2 + 3] + uVar6) {
          return 0;
        }
        uVar8 = param_2[uVar10 * 2 + 6];
        uVar6 = param_2[uVar10 * 2 + 7];
        if (uVar6 == 0 && uVar8 == 0) {
          uVar10 = uVar10 + 3;
          break;
        }
        if (uVar8 < param_2[uVar10 * 2 + 5] + uVar2) {
          return 0;
        }
        uVar2 = param_2[uVar10 * 2 + 8];
        uVar5 = param_2[uVar10 * 2 + 9];
        uVar10 = uVar10 + 4;
      } while ((uVar5 != 0) || (uVar2 != 0));
    }
    if (uVar10 != 0) {
      iVar3 = FUN_0800c844(puVar7 + 5);
      if ((iVar3 == 0) && (iVar3 = FUN_0800c808(puVar7 + 5), iVar3 != 0)) {
        if (uVar10 != 1) {
          uVar2 = uVar10 & 0xfffffffe;
          do {
            if (0xf < param_2[1]) {
              uVar6 = *param_2;
              uVar5 = param_2[1] & 0xfffffff8;
              iVar3 = 0;
              if ((uVar6 & 7) != 0) {
                iVar3 = 8 - (uVar6 & 7);
              }
              if (0xf < uVar5 - iVar3) {
                puVar9 = (undefined4 *)puVar7[2];
                puVar4 = (undefined4 *)(iVar3 + uVar6);
                if (puVar9 == (undefined4 *)0x0) {
                  *puVar7 = puVar4;
                  puVar7[1] = 0;
                  puVar9 = (undefined4 *)(uVar5 + uVar6 + -8);
                  *puVar9 = 0;
                  puVar7[2] = puVar9;
                  *(undefined4 *)(uVar5 + uVar6 + -4) = 0;
                  *puVar4 = puVar9;
                }
                else {
                  puVar1 = (undefined4 *)(uVar5 + uVar6 + -8);
                  *puVar1 = 0;
                  puVar7[2] = puVar1;
                  *(undefined4 *)(uVar5 + uVar6 + -4) = 0;
                  *puVar4 = puVar1;
                  *puVar9 = puVar4;
                }
                iVar3 = (uVar5 - iVar3) - 8;
                puVar4[1] = iVar3;
                puVar7[3] = iVar3 + puVar7[3];
                puVar7[4] = puVar7[4] + 1;
              }
            }
            if (0xf < param_2[3]) {
              uVar6 = param_2[2];
              uVar5 = param_2[3] & 0xfffffff8;
              iVar3 = 0;
              if ((uVar6 & 7) != 0) {
                iVar3 = 8 - (uVar6 & 7);
              }
              if (0xf < uVar5 - iVar3) {
                puVar9 = (undefined4 *)puVar7[2];
                puVar4 = (undefined4 *)(iVar3 + uVar6);
                if (puVar9 == (undefined4 *)0x0) {
                  *puVar7 = puVar4;
                  puVar7[1] = 0;
                  puVar9 = (undefined4 *)(uVar5 + uVar6 + -8);
                  *puVar9 = 0;
                  puVar7[2] = puVar9;
                  *(undefined4 *)(uVar5 + uVar6 + -4) = 0;
                  *puVar4 = puVar9;
                }
                else {
                  puVar1 = (undefined4 *)(uVar5 + uVar6 + -8);
                  *puVar1 = 0;
                  puVar7[2] = puVar1;
                  *(undefined4 *)(uVar5 + uVar6 + -4) = 0;
                  *puVar4 = puVar1;
                  *puVar9 = puVar4;
                }
                iVar3 = (uVar5 - iVar3) - 8;
                puVar4[1] = iVar3;
                puVar7[3] = iVar3 + puVar7[3];
                puVar7[4] = puVar7[4] + 1;
              }
            }
            uVar2 = uVar2 - 2;
            param_2 = param_2 + 4;
          } while (uVar2 != 0);
        }
        if (((uVar10 & 1) != 0) && (0xf < param_2[1])) {
          uVar2 = *param_2;
          uVar5 = param_2[1] & 0xfffffff8;
          iVar3 = 0;
          if ((uVar2 & 7) != 0) {
            iVar3 = 8 - (uVar2 & 7);
          }
          if (0xf < uVar5 - iVar3) {
            puVar9 = (undefined4 *)puVar7[2];
            puVar4 = (undefined4 *)(iVar3 + uVar2);
            if (puVar9 == (undefined4 *)0x0) {
              *puVar7 = puVar4;
              puVar9 = (undefined4 *)(uVar2 + uVar5 + -8);
              *puVar9 = 0;
              puVar7[1] = 0;
              puVar7[2] = puVar9;
              *(undefined4 *)(uVar2 + uVar5 + -4) = 0;
              *puVar4 = puVar9;
            }
            else {
              puVar1 = (undefined4 *)(uVar2 + uVar5 + -8);
              *puVar1 = 0;
              puVar7[2] = puVar1;
              *(undefined4 *)(uVar2 + uVar5 + -4) = 0;
              *puVar4 = puVar1;
              *puVar9 = puVar4;
            }
            iVar3 = (uVar5 - iVar3) - 8;
            puVar4[1] = iVar3;
            puVar7[3] = iVar3 + puVar7[3];
            puVar7[4] = puVar7[4] + 1;
          }
        }
        return puVar7[4];
      }
    }
  }
  return 0;
}



/* 0800c6f0 */

void FUN_0800c6f0(int *param_1,int param_2)

{
  int iVar1;
  int *piVar2;
  int *piVar3;
  int *piVar4;
  int *piVar5;
  int *piVar6;
  int *piVar7;
  uint uVar8;
  
  piVar7 = (int *)0x2001e3d0;
  if (param_1 != (int *)0x0) {
    piVar7 = param_1;
  }
  piVar6 = piVar7 + 5;
  FUN_0800c860(piVar6);
  piVar4 = (int *)(param_2 + -8);
  if (((param_2 == 0) || (-1 < (int)*(uint *)(param_2 + -4))) || (*piVar4 != -0x21524111)) {
LAB_0800c724:
    FUN_0800c850(piVar6);
    return;
  }
  uVar8 = *(uint *)(param_2 + -4) & 0x7fffffff;
  iVar1 = piVar7[3];
  *(uint *)(param_2 + -4) = uVar8;
  piVar7[3] = iVar1 + uVar8;
  piVar5 = piVar7;
  do {
    if (piVar5 == (int *)0x0) goto LAB_0800c724;
    piVar2 = (int *)*piVar5;
    piVar3 = piVar5;
    piVar5 = piVar2;
    if (piVar4 <= piVar2) break;
    if (piVar2 == (int *)0x0) goto LAB_0800c724;
    piVar5 = (int *)*piVar2;
    piVar3 = piVar2;
    if (piVar4 <= piVar5) break;
    if (piVar5 == (int *)0x0) goto LAB_0800c724;
    piVar2 = (int *)*piVar5;
    piVar3 = piVar5;
    piVar5 = piVar2;
    if (piVar4 <= piVar2) break;
    if (piVar2 == (int *)0x0) goto LAB_0800c724;
    piVar5 = (int *)*piVar2;
    piVar3 = piVar2;
  } while (piVar5 < piVar4);
  if ((int *)((int)piVar3 + piVar3[1]) == piVar4) {
    piVar3[1] = piVar3[1] + uVar8;
    piVar4 = piVar3;
  }
  piVar2 = piVar5;
  if (((piVar5[1] != 0) && ((int *)((int)piVar4 + piVar4[1]) == piVar5)) &&
     (piVar2 = (int *)piVar7[2], piVar5 != (int *)piVar7[2])) {
    piVar2 = (int *)*piVar5;
    piVar4[1] = piVar5[1] + piVar4[1];
  }
  *piVar4 = (int)piVar2;
  if (piVar3 != piVar4) {
    *piVar3 = (int)piVar4;
  }
  FUN_0800c850(piVar6);
  return;
}



/* 0800c7cc */

undefined4 FUN_0800c7cc(int param_1,undefined4 param_2,undefined4 param_3)

{
  undefined4 uVar1;
  
  if (param_1 == 0) {
    param_1 = 0x2001e3d0;
  }
  FUN_0800c860(param_1 + 0x14);
  uVar1 = FUN_0800ed1c(param_1,param_2,param_3);
  FUN_0800c850(param_1 + 0x14);
  return uVar1;
}



/* 0800c808 */

bool FUN_0800c808(int *param_1)

{
  int iVar1;
  undefined4 local_18;
  undefined4 local_14;
  undefined4 uStack_10;
  undefined4 local_c;
  
  local_18 = DAT_0800c834;
  local_c = DAT_0800c840;
  local_14 = DAT_0800c838;
  uStack_10 = DAT_0800c83c;
  iVar1 = FUN_0800d5c8(&local_18);
  *param_1 = iVar1;
  return iVar1 != 0;
}



/* 0800c844 */

bool FUN_0800c844(int *param_1)

{
  return *param_1 != 0;
}



/* 0800c850 */

bool FUN_0800c850(undefined4 *param_1)

{
  int iVar1;
  
  iVar1 = FUN_0800d63c(*param_1);
  return iVar1 == 0;
}



/* 0800c860 */

bool FUN_0800c860(undefined4 *param_1)

{
  int iVar1;
  
  iVar1 = FUN_0800d580(*param_1,0xffffffff);
  return iVar1 == 0;
}



/* 0800c874 */

/* WARNING: Restarted to delay deadcode elimination for space: stack */

int FUN_0800c874(int *param_1)

{
  uint uVar1;
  uint uVar2;
  
  if ((((param_1 == (int *)0x0) || (*param_1 != -0x21524111)) || (param_1[6] != 0x21524110)) ||
     ((param_1[1] == 0 || (param_1[2] == 0)))) {
    return 0;
  }
  uVar1 = param_1[3];
  uVar2 = param_1[4];
  if (uVar2 == uVar1) {
    return 0;
  }
  if (uVar2 <= uVar1) {
    return (param_1[2] - uVar1) + uVar2;
  }
  return uVar2 - uVar1;
}



/* 0800c8d4 */

undefined4 FUN_0800c8d4(undefined4 *param_1,int param_2,int param_3)

{
  if ((param_1 != (undefined4 *)0x0 && param_2 != 0) && (param_3 != 0)) {
    param_1[5] = 0;
    param_1[4] = 0;
    param_1[3] = 0;
    *param_1 = 0xdeadbeef;
    param_1[1] = param_2;
    param_1[2] = param_3;
    param_1[6] = 0x21524110;
    return 1;
  }
  return 0;
}



/* 0800c90c */

uint FUN_0800c90c(int *param_1,uint param_2,int param_3,uint param_4)

{
  int iVar1;
  uint uVar2;
  uint uVar3;
  int iVar4;
  uint uStack_20;
  
  if (param_1 == (int *)0x0) {
    return 0;
  }
  if (((*param_1 != -0x21524111) || (param_1[6] != 0x21524110)) || (iVar1 = param_1[1], iVar1 == 0))
  {
    return 0;
  }
  if ((param_4 != 0 && param_3 != 0) && (uVar2 = param_1[2], uVar2 != 0)) {
    uStack_20 = param_1[3];
    uVar3 = param_1[4];
    if (uVar3 != uStack_20) {
      if (uStack_20 < uVar3) {
        iVar4 = -uStack_20;
      }
      else {
        iVar4 = uVar2 - uStack_20;
      }
      if (uVar3 + iVar4 <= param_2) {
        return 0;
      }
      uStack_20 = uStack_20 + param_2;
      param_2 = (uVar3 + iVar4) - param_2;
      if (uVar2 <= uStack_20) {
        uStack_20 = uStack_20 - uVar2;
      }
      if (param_2 < param_4) {
        param_4 = param_2;
      }
      if (param_4 == 0) {
        return 0;
      }
      if (uVar2 - uStack_20 < param_4) {
        uVar2 = uVar2 - uStack_20;
        FUN_080006aa(param_3,iVar1 + uStack_20,uVar2);
        if (param_4 == uVar2) {
          return param_4;
        }
        iVar1 = param_1[1];
        param_3 = param_3 + uVar2;
        uVar2 = param_4 - uVar2;
      }
      else {
        iVar1 = uStack_20 + iVar1;
        uVar2 = param_4;
      }
      FUN_080006aa(param_3,iVar1,uVar2);
      return param_4;
    }
  }
  return 0;
}



/* 0800c914 */

uint FUN_0800c914(int *param_1,uint param_2,int param_3,uint param_4)

{
  int iVar1;
  uint uVar2;
  uint uVar3;
  int iVar4;
  uint local_20;
  
  if (((*param_1 != -0x21524111) || (param_1[6] != 0x21524110)) || (iVar1 = param_1[1], iVar1 == 0))
  {
    return 0;
  }
  if ((param_4 != 0 && param_3 != 0) && (uVar2 = param_1[2], uVar2 != 0)) {
    local_20 = param_1[3];
    uVar3 = param_1[4];
    if (uVar3 != local_20) {
      if (local_20 < uVar3) {
        iVar4 = -local_20;
      }
      else {
        iVar4 = uVar2 - local_20;
      }
      if (uVar3 + iVar4 <= param_2) {
        return 0;
      }
      local_20 = local_20 + param_2;
      param_2 = (uVar3 + iVar4) - param_2;
      if (uVar2 <= local_20) {
        local_20 = local_20 - uVar2;
      }
      if (param_2 < param_4) {
        param_4 = param_2;
      }
      if (param_4 == 0) {
        return 0;
      }
      if (uVar2 - local_20 < param_4) {
        uVar2 = uVar2 - local_20;
        FUN_080006aa(param_3,iVar1 + local_20,uVar2);
        if (param_4 == uVar2) {
          return param_4;
        }
        iVar1 = param_1[1];
        param_3 = param_3 + uVar2;
        uVar2 = param_4 - uVar2;
      }
      else {
        iVar1 = local_20 + iVar1;
        uVar2 = param_4;
      }
      FUN_080006aa(param_3,iVar1,uVar2);
      return param_4;
    }
  }
  return 0;
}



/* 0800ca00 */

uint FUN_0800ca00(int *param_1,int param_2,uint param_3)

{
  int iVar1;
  uint uVar2;
  int iVar3;
  uint uStack_28;
  
  if (param_1 == (int *)0x0) {
    return 0;
  }
  if (((*param_1 == -0x21524111) && (param_1[6] == 0x21524110)) && (param_1[1] != 0)) {
    if ((param_3 == 0 || param_2 == 0) || (iVar1 = param_1[2], iVar1 == 0)) {
      return 0;
    }
    uStack_28 = param_1[3];
    uVar2 = param_1[4];
    if (uVar2 != uStack_28) {
      if (uStack_28 < uVar2) {
        iVar3 = -uStack_28;
      }
      else {
        iVar3 = iVar1 - uStack_28;
      }
      uVar2 = uVar2 + iVar3;
      if (uVar2 < param_3) {
        param_3 = uVar2;
      }
      if (uVar2 != 0) {
        uVar2 = param_3;
        if (iVar1 - uStack_28 < param_3) {
          uVar2 = iVar1 - uStack_28;
        }
        FUN_080006aa(param_2,param_1[1] + uStack_28,uVar2);
        uStack_28 = uStack_28 + uVar2;
        if (param_3 != uVar2) {
          uStack_28 = param_3 - uVar2;
          FUN_080006aa(param_2 + uVar2,param_1[1],uStack_28);
        }
        if ((uint)param_1[2] <= uStack_28) {
          uStack_28 = 0;
        }
        param_1[3] = uStack_28;
        if ((code *)param_1[5] != (code *)0x0) {
          (*(code *)param_1[5])(param_1,0,param_3);
        }
        return param_3;
      }
    }
  }
  return 0;
}



/* 0800ca08 */

uint FUN_0800ca08(int *param_1,int param_2,uint param_3)

{
  int iVar1;
  uint uVar2;
  int iVar3;
  uint local_28;
  
  if (((*param_1 == -0x21524111) && (param_1[6] == 0x21524110)) && (param_1[1] != 0)) {
    if ((param_3 == 0 || param_2 == 0) || (iVar1 = param_1[2], iVar1 == 0)) {
      return 0;
    }
    local_28 = param_1[3];
    uVar2 = param_1[4];
    if (uVar2 != local_28) {
      if (local_28 < uVar2) {
        iVar3 = -local_28;
      }
      else {
        iVar3 = iVar1 - local_28;
      }
      uVar2 = uVar2 + iVar3;
      if (uVar2 < param_3) {
        param_3 = uVar2;
      }
      if (uVar2 != 0) {
        uVar2 = param_3;
        if (iVar1 - local_28 < param_3) {
          uVar2 = iVar1 - local_28;
        }
        FUN_080006aa(param_2,param_1[1] + local_28,uVar2);
        local_28 = local_28 + uVar2;
        if (param_3 != uVar2) {
          local_28 = param_3 - uVar2;
          FUN_080006aa(param_2 + uVar2,param_1[1],local_28);
        }
        if ((uint)param_1[2] <= local_28) {
          local_28 = 0;
        }
        param_1[3] = local_28;
        if ((code *)param_1[5] != (code *)0x0) {
          (*(code *)param_1[5])(param_1,0,param_3);
        }
        return param_3;
      }
    }
  }
  return 0;
}



/* 0800cafc */

uint FUN_0800cafc(int *param_1,uint param_2)

{
  uint uVar1;
  uint uVar2;
  uint local_14;
  
  if (param_1 == (int *)0x0) {
    uVar2 = 0;
  }
  else {
    if (((*param_1 != -0x21524111) || (param_1[6] != 0x21524110)) || (param_1[1] == 0)) {
      return 0;
    }
    uVar2 = 0;
    if ((param_2 != 0) && (uVar1 = param_1[2], uVar1 != 0)) {
      local_14 = param_1[3];
      uVar2 = param_1[4];
      if (uVar2 == local_14) {
        uVar2 = 0;
      }
      else if (local_14 < uVar2) {
        uVar2 = uVar2 - local_14;
      }
      else {
        uVar2 = uVar2 + (uVar1 - local_14);
      }
      if (param_2 < uVar2) {
        uVar2 = param_2;
      }
      local_14 = local_14 + uVar2;
      if (uVar1 <= local_14) {
        local_14 = local_14 - uVar1;
      }
      param_1[3] = local_14;
      if ((code *)param_1[5] != (code *)0x0) {
        (*(code *)param_1[5])(param_1,0,uVar2);
        return uVar2;
      }
    }
  }
  return uVar2;
}



/* 0800cb9c */

uint FUN_0800cb9c(int *param_1,int param_2,uint param_3)

{
  uint uVar1;
  int iVar2;
  int iVar3;
  uint local_24;
  
  if ((((param_1 == (int *)0x0) || (*param_1 != -0x21524111)) || (param_1[6] != 0x21524110)) ||
     (param_1[1] == 0)) {
    return 0;
  }
  if ((param_3 != 0 && param_2 != 0) && (iVar3 = param_1[2], iVar3 != 0)) {
    uVar1 = param_1[3];
    local_24 = param_1[4];
    iVar2 = iVar3;
    if (local_24 != uVar1) {
      if (local_24 < uVar1) {
        iVar2 = uVar1 - local_24;
      }
      else {
        iVar2 = (iVar3 - local_24) + uVar1;
      }
    }
    uVar1 = iVar2 - 1;
    if (uVar1 < param_3) {
      param_3 = uVar1;
    }
    if (uVar1 != 0) {
      uVar1 = param_3;
      if (iVar3 - local_24 < param_3) {
        uVar1 = iVar3 - local_24;
      }
      FUN_080006aa(local_24 + param_1[1],param_2,uVar1);
      local_24 = local_24 + uVar1;
      if (param_3 != uVar1) {
        local_24 = param_3 - uVar1;
        FUN_080006aa(param_1[1],param_2 + uVar1,local_24);
      }
      if ((uint)param_1[2] <= local_24) {
        local_24 = 0;
      }
      param_1[4] = local_24;
      if ((code *)param_1[5] == (code *)0x0) {
        return param_3;
      }
      (*(code *)param_1[5])(param_1,1,param_3);
      return param_3;
    }
  }
  return 0;
}



/* 0800cc9c */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_0800cc9c(void)

{
  _DAT_2001e3a0 = 0;
  FUN_08006c54();
  FUN_08006c54();
  FUN_0800c4f0(0,0x2001c084);
  FUN_08002c9c();
  FUN_08006f00();
  _DAT_40023840 = _DAT_40023840 | 0x300000;
  _DAT_40023830 = _DAT_40023830 | 0x200000;
  FUN_08006108(0x200000);
  FUN_08005e88();
  FUN_08006a84();
  FUN_08006388();
  FUN_08006614();
  FUN_08006770();
  FUN_080068b0();
  FUN_08006970();
  FUN_080063d0();
  FUN_0800645c();
  FUN_08006a3c();
  FUN_08006ac0();
  FUN_08006afc();
  FUN_08006b3c();
  FUN_0800691c();
  FUN_080067d8();
  FUN_08006844();
  FUN_08006590();
  FUN_08005e60();
  FUN_080064e8();
  FUN_08005dd4();
  FUN_0800635c();
  FUN_08002dec(0xb,5,0);
  FUN_08002dcc(0xb);
  FUN_08002dec(0xc,5,0);
  FUN_08002dcc(0xc);
  FUN_08002dec(0xe,5,0);
  FUN_08002dcc(0xe);
  FUN_08002dec(0xf,5,0);
  FUN_08002dcc(0xf);
  FUN_08002dec(0x10,5,0);
  FUN_08002dcc(0x10);
  FUN_08002dec(0x11,5,0);
  FUN_08002dcc(0x11);
  FUN_08002dec(0x1c,5,0);
  FUN_08002dcc(0x1c);
  FUN_08002dec(0x1d,5,0);
  FUN_08002dcc(0x1d);
  FUN_08002dec(0x1e,5,0);
  FUN_08002dcc(0x1e);
  FUN_08002dec(0x26,5,0);
  FUN_08002dcc(0x26);
  FUN_08002dec(0x27,5,0);
  FUN_08002dcc(0x27);
  FUN_08002dec(0x28,5,0);
  FUN_08002dcc(0x28);
  FUN_08002dec(0x2b,5,0);
  FUN_08002dcc(0x2b);
  FUN_08002dec(0x2c,5,0);
  FUN_08002dcc(0x2c);
  FUN_08002dec(0x32,5,0);
  FUN_08002dcc(0x32);
  FUN_08002dec(0x35,5,0);
  FUN_08002dcc(0x35);
  FUN_08002dec(0x37,5,0);
  FUN_08002dcc(0x37);
  FUN_08002dec(0x47,5,0);
  FUN_08002dcc(0x47);
  FUN_08002dec(0x4d,5,0);
  FUN_08002dcc(0x4d);
  if (_DAT_2001e3a0 == 0) {
    FUN_08000640(s_Start____0800cebc);
  }
  FUN_0800daac();
  FUN_080059a8();
  FUN_0800d368();
  FUN_08005ec0();
  FUN_0800d390();
  do {
                    /* WARNING: Do nothing block with infinite loop */
  } while( true );
}



/* 0800d310 */

undefined4 FUN_0800d310(int param_1)

{
  bool bVar1;
  uint uVar2;
  
  uVar2 = 0;
  bVar1 = (bool)isCurrentModePrivileged();
  if (bVar1) {
    uVar2 = getCurrentExceptionNumber();
    uVar2 = uVar2 & 0x1ff;
  }
  if (uVar2 == 0) {
    if (param_1 != 0) {
      FUN_08011678(param_1);
      return 0;
    }
    return 0;
  }
  return 0xfffffffa;
}



/* 0800d330 */

/* WARNING: Removing unreachable block (ram,0x08011adc) */
/* WARNING: Removing unreachable block (ram,0x08011ae0) */
/* WARNING: Removing unreachable block (ram,0x08011ae4) */
/* WARNING: Removing unreachable block (ram,0x08011aec) */

undefined4 * FUN_0800d330(int param_1)

{
  bool bVar1;
  undefined4 *puVar2;
  uint uVar3;
  
  uVar3 = 0;
  bVar1 = (bool)isCurrentModePrivileged();
  if (bVar1) {
    uVar3 = getCurrentExceptionNumber();
    uVar3 = uVar3 & 0x1ff;
  }
  if (uVar3 == 0) {
    if (param_1 == 0) {
LAB_08011a7c:
      puVar2 = (undefined4 *)FUN_0800ee94(0x20);
      if (puVar2 == (undefined4 *)0x0) {
        return (undefined4 *)0x0;
      }
      *puVar2 = 0;
      FUN_080112ac(puVar2 + 1);
      *(undefined1 *)(puVar2 + 7) = 0;
      return puVar2;
    }
    puVar2 = *(undefined4 **)(param_1 + 8);
    if (puVar2 == (undefined4 *)0x0) {
      if (*(uint *)(param_1 + 0xc) == 0) goto LAB_08011a7c;
    }
    else if (0x1f < *(uint *)(param_1 + 0xc)) {
      if (puVar2 == (undefined4 *)0x0) {
        bVar1 = (bool)isCurrentModePrivileged();
        if (bVar1) {
          setBasePriority(0x50);
        }
        InstructionSynchronizationBarrier(0xf);
        DataSynchronizationBarrier(0xf);
        do {
                    /* WARNING: Do nothing block with infinite loop */
        } while( true );
      }
      *puVar2 = 0;
      FUN_080112ac(puVar2 + 1);
      *(undefined1 *)(puVar2 + 7) = 1;
      return puVar2;
    }
  }
  return (undefined4 *)0x0;
}



/* 0800d358 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined4 FUN_0800d358(void)

{
  bool bVar1;
  uint uVar2;
  
  uVar2 = 0;
  bVar1 = (bool)isCurrentModePrivileged();
  if (bVar1) {
    uVar2 = getCurrentExceptionNumber();
    uVar2 = uVar2 & 0x1ff;
  }
  if (uVar2 == 0) {
    return _DAT_2001c280;
  }
  FUN_080114ec();
  return _DAT_2001c280;
}



/* 0800d368 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined4 FUN_0800d368(void)

{
  bool bVar1;
  uint uVar2;
  undefined4 uVar3;
  
  uVar2 = 0;
  bVar1 = (bool)isCurrentModePrivileged();
  if (bVar1) {
    uVar2 = getCurrentExceptionNumber();
    uVar2 = uVar2 & 0x1ff;
  }
  if (uVar2 == 0) {
    if (_DAT_2001c4ec == 0) {
      _DAT_2001c4ec = 1;
      uVar3 = 0;
    }
    else {
      uVar3 = 0xffffffff;
    }
    return uVar3;
  }
  return 0xfffffffa;
}



/* 0800d390 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined4 FUN_0800d390(void)

{
  bool bVar1;
  uint uVar2;
  
  uVar2 = 0;
  bVar1 = (bool)isCurrentModePrivileged();
  if (bVar1) {
    uVar2 = getCurrentExceptionNumber();
    uVar2 = uVar2 & 0x1ff;
  }
  if (uVar2 == 0) {
    if (_DAT_2001c4ec == 1) {
      DAT_e000ed1f = 0;
      _DAT_2001c4ec = 2;
      FUN_080118b0();
      return 0;
    }
    return 0xffffffff;
  }
  return 0xfffffffa;
}



/* 0800d3cc */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined4 FUN_0800d3cc(int param_1,int param_2,undefined4 param_3,int param_4)

{
  bool bVar1;
  int iVar2;
  undefined4 uVar3;
  uint uVar4;
  int local_c;
  
  uVar4 = 0;
  bVar1 = (bool)isCurrentModePrivileged();
  if (bVar1) {
    uVar4 = getCurrentExceptionNumber();
    uVar4 = uVar4 & 0x1ff;
  }
  if (uVar4 == 0) {
    if (param_2 == 0 || param_1 == 0) {
      return 0xfffffffc;
    }
    iVar2 = FUN_08012580(param_1,param_2,param_4);
    if (iVar2 != 1) {
      uVar3 = 0xfffffffe;
      if (param_4 == 0) {
        uVar3 = 0xfffffffd;
      }
      return uVar3;
    }
  }
  else {
    if ((param_2 == 0 || param_1 == 0) || param_4 != 0) {
      return 0xfffffffc;
    }
    local_c = 0;
    iVar2 = FUN_080127c0(param_1,param_2,&local_c);
    if (iVar2 != 1) {
      return 0xfffffffd;
    }
    if (local_c != 0) {
      _DAT_e000ed04 = 0x10000000;
      DataSynchronizationBarrier(0xf);
      InstructionSynchronizationBarrier(0xf);
      return 0;
    }
  }
  return 0;
}



/* 0800d45c */

int FUN_0800d45c(int param_1,int param_2,undefined4 *param_3)

{
  bool bVar1;
  int iVar2;
  uint uVar3;
  undefined4 uVar4;
  
  uVar4 = 0;
  uVar3 = 0;
  bVar1 = (bool)isCurrentModePrivileged();
  if (bVar1) {
    uVar3 = getCurrentExceptionNumber();
    uVar3 = uVar3 & 0x1ff;
  }
  if ((param_2 != 0 && param_1 != 0) && (uVar3 == 0)) {
    if (param_3 == (undefined4 *)0x0) {
      iVar2 = FUN_08011f18(param_1,param_2,0);
      if (iVar2 != 0) goto LAB_0800d4be;
    }
    else {
      if (param_3[2] == 0) {
        if (param_3[3] != 0) {
          return 0;
        }
        if (param_3[4] != 0) {
          return 0;
        }
        if (param_3[5] != 0) {
          return 0;
        }
        iVar2 = FUN_08011f18(param_1,param_2,0);
      }
      else {
        if ((uint)param_3[3] < 0x50) {
          return 0;
        }
        if (param_3[4] == 0) {
          return 0;
        }
        if ((uint)param_3[5] < (uint)(param_2 * param_1)) {
          return 0;
        }
        iVar2 = FUN_08011f9c(param_1,param_2,param_3[4],param_3[2],0);
      }
      if (iVar2 != 0) {
        uVar4 = *param_3;
LAB_0800d4be:
        FUN_0801154c(iVar2,uVar4);
        return iVar2;
      }
    }
  }
  return 0;
}



/* 0800d4f0 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined4 FUN_0800d4f0(int param_1,int param_2,undefined4 param_3,int param_4)

{
  bool bVar1;
  int iVar2;
  undefined4 uVar3;
  uint uVar4;
  int local_c;
  
  uVar4 = 0;
  bVar1 = (bool)isCurrentModePrivileged();
  if (bVar1) {
    uVar4 = getCurrentExceptionNumber();
    uVar4 = uVar4 & 0x1ff;
  }
  if (uVar4 == 0) {
    if (param_2 != 0 && param_1 != 0) {
      iVar2 = FUN_08012078(param_1,param_2,param_4,0);
      uVar3 = 0;
      if ((iVar2 != 1) && (uVar3 = 0xfffffffe, param_4 == 0)) {
        uVar3 = 0xfffffffd;
      }
      return uVar3;
    }
  }
  else if ((param_2 != 0 && param_1 != 0) && param_4 == 0) {
    local_c = 0;
    iVar2 = FUN_08012338(param_1,param_2,&local_c,0);
    if (iVar2 == 1) {
      if (local_c != 0) {
        _DAT_e000ed04 = 0x10000000;
        DataSynchronizationBarrier(0xf);
        InstructionSynchronizationBarrier(0xf);
      }
      return 0;
    }
    return 0xfffffffd;
  }
  return 0xfffffffc;
}



/* 0800d580 */

undefined4 FUN_0800d580(uint param_1,int param_2)

{
  bool bVar1;
  int iVar2;
  undefined4 uVar3;
  uint uVar4;
  
  uVar4 = 0;
  bVar1 = (bool)isCurrentModePrivileged();
  if (bVar1) {
    uVar4 = getCurrentExceptionNumber();
    uVar4 = uVar4 & 0x1ff;
  }
  if (uVar4 != 0) {
    return 0xfffffffa;
  }
  if ((param_1 & 0xfffffffe) == 0) {
    return 0xfffffffc;
  }
  if ((param_1 & 1) == 0) {
    iVar2 = FUN_08012894();
  }
  else {
    iVar2 = FUN_08012b20(param_1 & 0xfffffffe);
  }
  if (iVar2 != 1) {
    uVar3 = 0xfffffffe;
    if (param_2 == 0) {
      uVar3 = 0xfffffffd;
    }
    return uVar3;
  }
  return 0;
}



/* 0800d59c */

undefined4 FUN_0800d59c(undefined4 param_1,int param_2,uint param_3)

{
  int iVar1;
  undefined4 uVar2;
  
  if ((param_3 & 1) == 0) {
    iVar1 = FUN_08012894();
  }
  else {
    iVar1 = FUN_08012b20();
  }
  if (iVar1 != 1) {
    uVar2 = 0xfffffffe;
    if (param_2 == 0) {
      uVar2 = 0xfffffffd;
    }
    return uVar2;
  }
  return 0;
}



/* 0800d5c8 */

uint FUN_0800d5c8(undefined4 *param_1)

{
  bool bVar1;
  uint uVar2;
  undefined4 uVar3;
  
  uVar2 = 0;
  bVar1 = (bool)isCurrentModePrivileged();
  if (bVar1) {
    uVar2 = getCurrentExceptionNumber();
    uVar2 = uVar2 & 0x1ff;
  }
  if (uVar2 != 0) {
    return 0;
  }
  if (param_1 == (undefined4 *)0x0) {
LAB_0800d5fc:
    uVar2 = FUN_08011e04(1);
  }
  else {
    uVar2 = param_1[1];
    if ((int)(uVar2 << 0x1c) < 0) {
      return 0;
    }
    if (param_1[2] == 0) {
      if (param_1[3] != 0) {
        return 0;
      }
      if ((uVar2 & 1) != 0) {
        uVar2 = FUN_08011e04(4);
        bVar1 = true;
        goto LAB_0800d606;
      }
      goto LAB_0800d5fc;
    }
    if ((uint)param_1[3] < 0x50) {
      return 0;
    }
    if ((uVar2 & 1) != 0) {
      uVar2 = FUN_08011e74(4);
      bVar1 = true;
      goto LAB_0800d606;
    }
    uVar2 = FUN_08011e74(1);
  }
  bVar1 = false;
LAB_0800d606:
  if (uVar2 == 0) {
    return 0;
  }
  if (param_1 == (undefined4 *)0x0) {
    uVar3 = 0;
  }
  else {
    uVar3 = *param_1;
  }
  FUN_0801154c(uVar2,uVar3);
  if (bVar1) {
    uVar2 = uVar2 | 1;
  }
  return uVar2;
}



/* 0800d63c */

undefined4 FUN_0800d63c(uint param_1)

{
  bool bVar1;
  int iVar2;
  undefined4 uVar3;
  uint uVar4;
  
  uVar4 = 0;
  bVar1 = (bool)isCurrentModePrivileged();
  if (bVar1) {
    uVar4 = getCurrentExceptionNumber();
    uVar4 = uVar4 & 0x1ff;
  }
  if (uVar4 != 0) {
    return 0xfffffffa;
  }
  uVar4 = param_1 & 0xfffffffe;
  if (uVar4 == 0) {
    return 0xfffffffc;
  }
  if ((param_1 & 1) != 0) {
    iVar2 = FUN_0801253c(uVar4);
    uVar3 = 0;
    if (iVar2 != 1) {
      uVar3 = 0xfffffffd;
    }
    return uVar3;
  }
  iVar2 = FUN_08012078(uVar4,0,0,0);
  uVar3 = 0;
  if (iVar2 != 1) {
    uVar3 = 0xfffffffd;
  }
  return uVar3;
}



/* 0800d684 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined4 FUN_0800d684(int param_1,int param_2)

{
  bool bVar1;
  undefined4 uVar2;
  int iVar3;
  uint uVar4;
  int local_c;
  
  if (param_1 == 0) {
    return 0xfffffffc;
  }
  uVar4 = 0;
  bVar1 = (bool)isCurrentModePrivileged();
  if (bVar1) {
    uVar4 = getCurrentExceptionNumber();
    uVar4 = uVar4 & 0x1ff;
  }
  if (uVar4 == 0) {
    iVar3 = FUN_08012894();
    if (iVar3 != 1) {
      uVar2 = 0xfffffffe;
      if (param_2 == 0) {
        uVar2 = 0xfffffffd;
      }
      return uVar2;
    }
  }
  else {
    if (param_2 != 0) {
      return 0xfffffffc;
    }
    local_c = 0;
    iVar3 = FUN_080127c0(param_1,0,&local_c);
    if (iVar3 != 1) {
      return 0xfffffffd;
    }
    if (local_c != 0) {
      _DAT_e000ed04 = 0x10000000;
      DataSynchronizationBarrier(0xf);
      InstructionSynchronizationBarrier(0xf);
    }
  }
  return 0;
}



/* 0800d6f0 */

int FUN_0800d6f0(uint param_1,uint param_2,undefined4 *param_3)

{
  bool bVar1;
  int iVar2;
  int iVar3;
  undefined4 uVar4;
  uint uVar5;
  
  uVar5 = 0;
  bVar1 = (bool)isCurrentModePrivileged();
  if (bVar1) {
    uVar5 = getCurrentExceptionNumber();
    uVar5 = uVar5 & 0x1ff;
  }
  if (param_1 < param_2) {
    return 0;
  }
  if (param_1 == 0) {
    return 0;
  }
  if (uVar5 != 0) {
    return 0;
  }
  if (param_3 == (undefined4 *)0x0) {
LAB_0800d738:
    if (param_1 == 1) {
      iVar2 = FUN_08011f18(1,0,3);
LAB_0800d74a:
      if (param_2 != 0 && iVar2 != 0) {
        iVar3 = FUN_08012078(iVar2,0,0,0);
        if (iVar3 != 1) {
          FUN_080115a4(iVar2);
          return 0;
        }
        goto LAB_0800d76e;
      }
    }
    else {
      iVar2 = FUN_08011ca8();
    }
  }
  else {
    if (param_3[2] == 0) {
      if (param_3[3] != 0) {
        return 0;
      }
      goto LAB_0800d738;
    }
    if ((uint)param_3[3] < 0x50) {
      return 0;
    }
    if (param_1 == 1) {
      iVar2 = FUN_08011f9c(1,0,0,param_3[2],3);
      goto LAB_0800d74a;
    }
    iVar2 = FUN_08011d40(param_1,param_2,param_3[2]);
  }
  if (iVar2 == 0) {
    return 0;
  }
LAB_0800d76e:
  if (param_3 == (undefined4 *)0x0) {
    uVar4 = 0;
  }
  else {
    uVar4 = *param_3;
  }
  FUN_0801154c(iVar2,uVar4);
  return iVar2;
}



/* 0800d7a8 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined4 FUN_0800d7a8(int param_1)

{
  bool bVar1;
  int iVar2;
  undefined4 uVar3;
  uint uVar4;
  int local_c;
  
  if (param_1 == 0) {
    return 0xfffffffc;
  }
  uVar4 = 0;
  bVar1 = (bool)isCurrentModePrivileged();
  if (bVar1) {
    uVar4 = getCurrentExceptionNumber();
    uVar4 = uVar4 & 0x1ff;
  }
  if (uVar4 == 0) {
    iVar2 = FUN_08012078(param_1,0,0,0);
    uVar3 = 0;
    if (iVar2 != 1) {
      uVar3 = 0xfffffffd;
    }
    return uVar3;
  }
  local_c = 0;
  iVar2 = FUN_08012480(param_1,&local_c);
  if (iVar2 != 1) {
    return 0xfffffffd;
  }
  if (local_c != 0) {
    _DAT_e000ed04 = 0x10000000;
    DataSynchronizationBarrier(0xf);
    InstructionSynchronizationBarrier(0xf);
  }
  return 0;
}



/* 0800d80c */

undefined4 FUN_0800d80c(int param_1,undefined4 param_2,undefined4 *param_3)

{
  bool bVar1;
  int iVar2;
  uint uVar3;
  undefined4 uVar4;
  undefined2 uVar5;
  uint uVar6;
  uint uVar7;
  undefined4 local_18;
  
  local_18 = 0;
  uVar3 = 0;
  bVar1 = (bool)isCurrentModePrivileged();
  if (bVar1) {
    uVar3 = getCurrentExceptionNumber();
    uVar3 = uVar3 & 0x1ff;
  }
  if (param_1 == 0) {
    return 0;
  }
  if (uVar3 != 0) {
    return 0;
  }
  if (param_3 == (undefined4 *)0x0) {
    uVar5 = 0x80;
    uVar3 = 0x18;
    uVar4 = 0;
  }
  else {
    uVar3 = param_3[6];
    if (uVar3 == 0) {
      uVar3 = 0x18;
    }
    if (0x38 < uVar3) {
      return 0;
    }
    if ((*(byte *)(param_3 + 1) & 1) != 0) {
      return 0;
    }
    uVar7 = param_3[5];
    uVar4 = *param_3;
    uVar6 = uVar7 >> 2;
    if (uVar7 == 0) {
      uVar6 = 0x80;
    }
    uVar5 = (undefined2)uVar6;
    if (param_3[2] != 0) {
      if ((uint)param_3[3] < 0x5c) {
        return 0;
      }
      if (param_3[4] == 0 || uVar7 == 0) {
        return 0;
      }
      uVar4 = FUN_08012c64(param_1,uVar4,uVar7 >> 2,param_2,uVar3,param_3[4],param_3[2]);
      return uVar4;
    }
    if ((param_3[3] != 0) || (param_3[4] != 0)) {
      return 0;
    }
  }
  iVar2 = FUN_08012c04(param_1,uVar4,uVar5,param_2,uVar3,&local_18);
  uVar4 = 0;
  if (iVar2 == 1) {
    uVar4 = local_18;
  }
  return uVar4;
}



/* 0800d8a0 */

int FUN_0800d8a0(int param_1,int param_2,int param_3,undefined4 *param_4)

{
  bool bVar1;
  int *piVar2;
  undefined4 uVar3;
  int iVar4;
  uint uVar5;
  
  uVar5 = 0;
  bVar1 = (bool)isCurrentModePrivileged();
  if (bVar1) {
    uVar5 = getCurrentExceptionNumber();
    uVar5 = uVar5 & 0x1ff;
  }
  if (param_1 == 0) {
    return 0;
  }
  if (uVar5 != 0) {
    return 0;
  }
  piVar2 = (int *)FUN_0800ee94(8);
  if (piVar2 == (int *)0x0) {
    return 0;
  }
  *piVar2 = param_1;
  piVar2[1] = param_3;
  if (param_4 == (undefined4 *)0x0) {
    uVar3 = 0;
LAB_0800d8fe:
    iVar4 = FUN_080130c0(uVar3,1,param_2 != 0,piVar2,0x80073a1);
  }
  else {
    uVar3 = *param_4;
    if (param_4[2] == 0) {
      if (param_4[3] != 0) goto LAB_0800d91c;
      goto LAB_0800d8fe;
    }
    if ((uint)param_4[3] < 0x2c) goto LAB_0800d91c;
    iVar4 = FUN_080130fc(uVar3,1,param_2 != 0,piVar2,0x80073a1,param_4[2]);
  }
  if (iVar4 != 0) {
    return iVar4;
  }
LAB_0800d91c:
  FUN_080113d8(piVar2);
  return 0;
}



/* 0800d946 */

undefined4 FUN_0800d946(undefined4 param_1,undefined4 param_2,undefined4 param_3)

{
  int iVar1;
  undefined4 uVar2;
  
  iVar1 = FUN_08013204(param_1,4,param_3,0,0);
  uVar2 = 0;
  if (iVar1 != 1) {
    uVar2 = 0xfffffffd;
  }
  return uVar2;
}



/* 0800d968 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_0800d968(int param_1)

{
  FUN_0800bce0(_DAT_2001c3f0,*(undefined2 *)(param_1 + 4),*(undefined2 *)(param_1 + 6),
               *(undefined2 *)(param_1 + 8),*(undefined2 *)(param_1 + 10));
  return;
}



/* 0800d990 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_0800d990(undefined4 param_1,uint param_2)

{
  FUN_0800cb9c(_DAT_2001e5b0,_DAT_2001e5a4 + _DAT_2001e5bc,param_2 - _DAT_2001e5bc);
  if (0xff < param_2) {
    param_2 = 0;
  }
  _DAT_2001e5bc = param_2;
  FUN_0800d7a8(_DAT_2001c204);
  return;
}



/* 0800daac */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_0800daac(void)

{
  FUN_08000788(0x2001e468,0x154);
  _DAT_2001e5a4 = 0x2001e5c0;
  _DAT_2001e5a8 = 0x100;
  _DAT_2001e5ac = FUN_0800c7cc(0,0x2001c084,0x800);
  _DAT_2001e5b0 = FUN_0800c7cc(0,0x2001c084,0x1c);
  FUN_0800c8d4(_DAT_2001e5b0,_DAT_2001e5ac,0x800);
  _DAT_2001e5b4 = &LAB_0800f600_1;
  return;
}



/* 0800ddac */

void FUN_0800ddac(uint *param_1)

{
  byte bVar1;
  char cVar2;
  uint uVar3;
  int iVar4;
  byte *pbVar5;
  byte *pbVar6;
  byte local_64 [64];
  
  uVar3 = FUN_0800c874(param_1[0x52]);
  if (uVar3 != 0) {
    pbVar5 = (byte *)((int)param_1 + 6);
    do {
      if (0x3f < uVar3) {
        uVar3 = 0x40;
      }
      iVar4 = FUN_0800ca00(param_1[0x52],local_64,uVar3);
      if (iVar4 != 0) {
        pbVar6 = local_64;
        do {
          switch(*param_1) {
          case 0:
            *param_1 = (uint)(*pbVar6 == 0xaa);
            break;
          case 1:
            *param_1 = (uint)(*pbVar6 == 0x55) << 1;
            break;
          case 2:
            bVar1 = *pbVar6;
            uVar3 = 0;
            if (bVar1 < 0xb) {
              uVar3 = 3;
            }
            *param_1 = uVar3;
            if (bVar1 < 0xb) {
              *pbVar5 = bVar1;
            }
            break;
          case 3:
            bVar1 = *pbVar6;
            *(byte *)((int)param_1 + 7) = bVar1;
            uVar3 = 4;
            if (bVar1 == 0) {
              uVar3 = 5;
            }
            *param_1 = uVar3;
            param_1[0x4e] = 0;
            break;
          case 4:
            *(byte *)((int)param_1 + param_1[0x4e] + 8) = *pbVar6;
            uVar3 = param_1[0x4e];
            param_1[0x4e] = uVar3 + 1;
            if ((int)(uint)*(byte *)((int)param_1 + 7) <= (int)(uVar3 + 1)) {
              *param_1 = 5;
            }
            break;
          case 5:
            bVar1 = *(byte *)((int)param_1 + 7);
            *(byte *)((int)param_1 + bVar1 + 8) = *pbVar6;
            cVar2 = FUN_0800be78(pbVar5,bVar1 + 2);
            if ((*(char *)((int)param_1 + *(byte *)((int)param_1 + 7) + 8) == cVar2) &&
               ((code *)param_1[*pbVar5 + 0x43] != (code *)0x0)) {
              (*(code *)param_1[*pbVar5 + 0x43])(param_1 + 1);
            }
            FUN_08000788(param_1,0x109);
            break;
          default:
            *param_1 = 0;
          }
          iVar4 = iVar4 + -1;
          pbVar6 = pbVar6 + 1;
        } while (iVar4 != 0);
      }
      uVar3 = FUN_0800c874(param_1[0x52]);
    } while (uVar3 != 0);
  }
  return;
}



/* 0800e274 */

undefined4 FUN_0800e274(int param_1,undefined1 param_2,undefined4 param_3,int param_4)

{
  undefined1 uVar1;
  undefined2 *puVar2;
  undefined4 uVar3;
  
  puVar2 = (undefined2 *)FUN_0800c7cc(0,0x2001c08c,param_4 + 6);
  if (puVar2 != (undefined2 *)0x0) {
    *(undefined1 *)(puVar2 + 1) = param_2;
    *puVar2 = 0x55aa;
    *(char *)((int)puVar2 + 3) = (char)param_4;
    FUN_080006aa(puVar2 + 2,param_3,param_4);
    uVar1 = FUN_0800be78(puVar2 + 1,param_4 + 2U & 0xffff);
    *(undefined1 *)((int)(puVar2 + 2) + param_4) = uVar1;
                    /* WARNING: Could not recover jumptable at 0x0800e2ce. Too many branches */
                    /* WARNING: Treating indirect jump as call */
    uVar3 = (**(code **)(param_1 + 0x14c))(param_1,puVar2);
    return uVar3;
  }
  return 0xfffffffe;
}



/* 0800e3a4 */

void FUN_0800e3a4(float param_1,float param_2,float *param_3)

{
  float fVar1;
  float fVar2;
  
  fVar2 = param_3[5];
  fVar1 = param_3[4];
  param_1 = *param_3 - param_1;
  param_3[4] = param_1;
  param_3[5] = fVar1;
  param_3[6] = param_3[3] * ((fVar1 + (param_1 - (fVar2 + fVar2))) / param_2) +
               param_3[1] * param_1 + param_2 * param_1 * param_3[2];
  return;
}



/* 0800e3f8 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_0800e3f8(int param_1)

{
  uint uVar1;
  uint uVar2;
  
  FUN_08011360();
  _DAT_2001c274 = _DAT_2001c274 + 1;
  if (_DAT_2001c268 == 0) {
    _DAT_2001c268 = param_1;
    if (_DAT_2001c274 == 1) {
      FUN_080112ac(&DAT_2001e910);
      FUN_080112ac(0x2001e924);
      FUN_080112ac(0x2001e938);
      FUN_080112ac(0x2001e94c);
      FUN_080112ac(0x2001e960);
      FUN_080112ac(0x2001e974);
      FUN_080112ac(0x2001e988);
      FUN_080112ac(0x2001e99c);
      FUN_080112ac(0x2001e9b0);
      FUN_080112ac(0x2001e9c4);
      FUN_080112ac(0x2001e9d8);
      FUN_080112ac(0x2001e9ec);
      FUN_080112ac(0x2001ea00);
      FUN_080112ac(0x2001ea14);
      FUN_080112ac(0x2001ea28);
      FUN_080112ac(0x2001ea3c);
      FUN_080112ac(0x2001ea50);
      FUN_080112ac(0x2001ea64);
      FUN_080112ac(0x2001ea78);
      FUN_080112ac(0x2001ea8c);
      FUN_080112ac(0x2001eaa0);
      FUN_080112ac(0x2001eab4);
      FUN_080112ac(0x2001eac8);
      FUN_080112ac(0x2001eadc);
      FUN_080112ac(0x2001eaf0);
      FUN_080112ac(0x2001eb04);
      FUN_080112ac(0x2001eb18);
      FUN_080112ac(0x2001eb2c);
      FUN_080112ac(0x2001eb40);
      FUN_080112ac(0x2001eb54);
      FUN_080112ac(0x2001eb68);
      FUN_080112ac(0x2001eb7c);
      FUN_080112ac(0x2001eb90);
      FUN_080112ac(0x2001eba4);
      FUN_080112ac(0x2001ebb8);
      FUN_080112ac(0x2001ebcc);
      FUN_080112ac(0x2001ebe0);
      FUN_080112ac(0x2001ebf4);
      FUN_080112ac(0x2001ec08);
      FUN_080112ac(0x2001ec1c);
      FUN_080112ac(0x2001ec30);
      FUN_080112ac(0x2001ec44);
      FUN_080112ac(0x2001ec58);
      FUN_080112ac(0x2001ec6c);
      FUN_080112ac(0x2001ec80);
      FUN_080112ac(0x2001ec94);
      FUN_080112ac(0x2001eca8);
      FUN_080112ac(0x2001ecbc);
      FUN_080112ac(0x2001ecd0);
      FUN_080112ac(0x2001ece4);
      FUN_080112ac(0x2001ecf8);
      FUN_080112ac(0x2001ed0c);
      FUN_080112ac(0x2001ed20);
      FUN_080112ac(0x2001ed34);
      FUN_080112ac(0x2001ed48);
      FUN_080112ac(0x2001ed5c);
      FUN_080112ac(0x2001c4c0);
      FUN_080112ac(0x2001c4d4);
      FUN_080112ac(&DAT_2001c2cc);
      FUN_080112ac(0x2001c2a4);
      FUN_080112ac(0x2001c2b8);
      _DAT_2001c284 = 0x2001c4c0;
      _DAT_2001c288 = 0x2001c4d4;
    }
  }
  else if ((_DAT_2001c278 == 0) && (*(uint *)(_DAT_2001c268 + 0x2c) <= *(uint *)(param_1 + 0x2c))) {
    _DAT_2001c268 = param_1;
  }
  uVar1 = _DAT_2001c28c;
  _DAT_2001c26c = _DAT_2001c26c + 1;
  uVar2 = *(uint *)(param_1 + 0x2c);
  *(int *)(param_1 + 0x44) = _DAT_2001c26c;
  if (uVar1 < uVar2) {
    _DAT_2001c28c = uVar2;
  }
  FUN_08011330(&DAT_2001e910 + uVar2 * 0x14,param_1 + 4);
  FUN_080113a8();
  if (_DAT_2001c278 != 0) {
    if (*(uint *)(param_1 + 0x2c) <= *(uint *)(_DAT_2001c268 + 0x2c)) {
      return;
    }
    _DAT_e000ed04 = 0x10000000;
    DataSynchronizationBarrier(0xf);
    InstructionSynchronizationBarrier(0xf);
  }
  return;
}



/* 0800e710 */

void FUN_0800e710(undefined4 param_1,char *param_2,int param_3,undefined4 param_4,uint param_5,
                 undefined4 *param_6,undefined4 *param_7)

{
  char cVar1;
  int iVar2;
  undefined4 uVar3;
  
  FUN_08000734(param_7[0xc],param_3 << 2,0xa5);
  iVar2 = param_7[0xc];
  if (param_2 == (char *)0x0) {
    *(undefined1 *)(param_7 + 0xd) = 0;
  }
  else {
    cVar1 = *param_2;
    *(char *)(param_7 + 0xd) = cVar1;
    if (((((cVar1 != '\0') &&
          (cVar1 = param_2[1], *(char *)((int)param_7 + 0x35) = cVar1, cVar1 != '\0')) &&
         (cVar1 = param_2[2], *(char *)((int)param_7 + 0x36) = cVar1, cVar1 != '\0')) &&
        (((cVar1 = param_2[3], *(char *)((int)param_7 + 0x37) = cVar1, cVar1 != '\0' &&
          (cVar1 = param_2[4], *(char *)(param_7 + 0xe) = cVar1, cVar1 != '\0')) &&
         ((cVar1 = param_2[5], *(char *)((int)param_7 + 0x39) = cVar1, cVar1 != '\0' &&
          ((cVar1 = param_2[6], *(char *)((int)param_7 + 0x3a) = cVar1, cVar1 != '\0' &&
           (cVar1 = param_2[7], *(char *)((int)param_7 + 0x3b) = cVar1, cVar1 != '\0')))))))) &&
       ((cVar1 = param_2[8], *(char *)(param_7 + 0xf) = cVar1, cVar1 != '\0' &&
        (((((cVar1 = param_2[9], *(char *)((int)param_7 + 0x3d) = cVar1, cVar1 != '\0' &&
            (cVar1 = param_2[10], *(char *)((int)param_7 + 0x3e) = cVar1, cVar1 != '\0')) &&
           (cVar1 = param_2[0xb], *(char *)((int)param_7 + 0x3f) = cVar1, cVar1 != '\0')) &&
          ((cVar1 = param_2[0xc], *(char *)(param_7 + 0x10) = cVar1, cVar1 != '\0' &&
           (cVar1 = param_2[0xd], *(char *)((int)param_7 + 0x41) = cVar1, cVar1 != '\0')))) &&
         (cVar1 = param_2[0xe], *(char *)((int)param_7 + 0x42) = cVar1, cVar1 != '\0')))))) {
      *(char *)((int)param_7 + 0x43) = param_2[0xf];
    }
    *(undefined1 *)((int)param_7 + 0x43) = 0;
  }
  if (0x36 < param_5) {
    param_5 = 0x37;
  }
  param_7[0xb] = param_5;
  param_7[0x13] = param_5;
  param_7[0x14] = 0;
  FUN_080112c4(param_7 + 1);
  FUN_080112c4(param_7 + 6);
  param_7[6] = 0x38 - param_5;
  param_7[4] = param_7;
  param_7[9] = param_7;
  param_7[0x15] = 0;
  *(undefined1 *)(param_7 + 0x16) = 0;
  uVar3 = FUN_0800f2a0((iVar2 + param_3 * 4) - 4U & 0xfffffff8,param_1,param_4);
  *param_7 = uVar3;
  if (param_6 != (undefined4 *)0x0) {
    *param_6 = param_7;
  }
  return;
}



/* 0800e814 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_0800e814(undefined4 param_1,int param_2,int param_3,undefined4 param_4,undefined4 param_5,
                 undefined4 *param_6)

{
  bool bVar1;
  
  if (param_2 != 0) {
    FUN_08011360();
    if (_DAT_2001c2e0 == 0) {
      FUN_080112ac(0x2001c2f4);
      FUN_080112ac(0x2001c308);
      _DAT_2001c2e8 = 0x2001c2f4;
      _DAT_2001c2ec = 0x2001c308;
      _DAT_2001c2e0 = FUN_08011f9c(10,0x10,0x2001e810,0x2001e8b0,0);
      if (_DAT_2001c2e0 != 0) {
        FUN_0801154c(_DAT_2001c2e0,&LAB_08013846_1);
      }
    }
    FUN_080113a8();
    *param_6 = param_1;
    param_6[6] = param_2;
    param_6[7] = param_4;
    param_6[8] = param_5;
    FUN_080112c4(param_6 + 1);
    if (param_3 != 0) {
      *(byte *)(param_6 + 10) = *(byte *)(param_6 + 10) | 4;
    }
    return;
  }
  bVar1 = (bool)isCurrentModePrivileged();
  if (bVar1) {
    setBasePriority(0x50);
  }
  InstructionSynchronizationBarrier(0xf);
  DataSynchronizationBarrier(0xf);
  do {
                    /* WARNING: Do nothing block with infinite loop */
  } while( true );
}



/* 0800e8c4 */

/* WARNING: Removing unreachable block (ram,0x0800e926) */
/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_0800e8c4(void)

{
  bool bVar1;
  char cVar2;
  undefined4 unaff_r8;
  undefined4 in_cr14;
  
  bVar1 = (bool)isCurrentModePrivileged();
  if (bVar1) {
    setMainStackPointer(*(undefined4 *)*puRam0800e8e8);
  }
  bVar1 = (bool)isCurrentModePrivileged();
  if (bVar1) {
    setThreadModePrivileged(1);
    bVar1 = (bool)isThreadMode();
    if (bVar1) {
      cVar2 = isUsingMainStack();
      setStackMode(cVar2 == '\x01');
    }
  }
  enableIRQinterrupts();
  enableFIQinterrupts();
  DataSynchronizationBarrier(0xf);
  InstructionSynchronizationBarrier(0xf);
  software_interrupt(0);
  coprocessor_store(0,in_cr14,unaff_r8);
  bVar1 = (bool)isCurrentModePrivileged();
  if (bVar1) {
    setBasePriority(0x50);
  }
  InstructionSynchronizationBarrier(0xf);
  DataSynchronizationBarrier(0xf);
  if (_DAT_2001c09c == -1) {
    do {
    } while( true );
  }
  do {
                    /* WARNING: Do nothing block with infinite loop */
  } while( true );
}



/* 0800eca8 */

void FUN_0800eca8(int param_1)

{
  int iVar1;
  uint uVar2;
  uint uVar3;
  
  FUN_08011360();
  uVar3 = (uint)*(char *)(param_1 + 0x45);
  if (0 < (int)uVar3) {
    do {
      if (*(int *)(param_1 + 0x24) == 0) break;
      iVar1 = FUN_08012f5c((int *)(param_1 + 0x24));
      if (iVar1 != 0) {
        FUN_0801170c();
      }
      uVar2 = uVar3 & 0xff;
      uVar3 = uVar3 - 1;
    } while (1 < uVar2);
  }
  *(undefined1 *)(param_1 + 0x45) = 0xff;
  FUN_080113a8();
  FUN_08011360();
  uVar3 = (uint)*(char *)(param_1 + 0x44);
  if (0 < (int)uVar3) {
    do {
      if (*(int *)(param_1 + 0x10) == 0) break;
      iVar1 = FUN_08012f5c((int *)(param_1 + 0x10));
      if (iVar1 != 0) {
        FUN_0801170c();
      }
      uVar2 = uVar3 & 0xff;
      uVar3 = uVar3 - 1;
    } while (1 < uVar2);
  }
  *(undefined1 *)(param_1 + 0x44) = 0xff;
  FUN_080113a8();
  return;
}



/* 0800ed1c */

undefined4 * FUN_0800ed1c(undefined4 *param_1,uint *param_2,int param_3)

{
  undefined4 *puVar1;
  uint uVar2;
  undefined4 *puVar3;
  uint uVar4;
  uint uVar5;
  undefined4 *puVar6;
  int iVar7;
  int iVar8;
  uint uVar9;
  undefined4 *puVar10;
  undefined4 *puVar11;
  
  uVar2 = param_3 + 7U & 0xfffffff8;
  uVar4 = uVar2 + 8;
  if ((int)uVar4 < 0) {
    return (undefined4 *)0x0;
  }
  if (uVar2 == 0) {
    return (undefined4 *)0x0;
  }
  puVar11 = (undefined4 *)param_1[2];
  if (puVar11 == (undefined4 *)0x0) {
    return (undefined4 *)0x0;
  }
  puVar3 = (undefined4 *)*param_1;
  puVar1 = param_1;
  if (param_2 != (uint *)0x0) {
    if (0xf < param_2[1]) {
      uVar2 = *param_2;
      uVar5 = param_2[1] & 0xfffffff8;
      iVar8 = 0;
      if ((uVar2 & 7) != 0) {
        iVar8 = 8 - (uVar2 & 7);
      }
      if ((0xf < uVar5 - iVar8) && (puVar3 != (undefined4 *)0x0)) {
        if (puVar3 == puVar11) {
          return (undefined4 *)0x0;
        }
        if ((undefined4 *)*puVar3 == (undefined4 *)0x0) {
          return (undefined4 *)0x0;
        }
        puVar6 = (undefined4 *)*puVar3;
        do {
          if ((undefined4 *)(iVar8 + uVar2) <= puVar3) {
            if ((undefined4 *)(uVar2 + uVar5) <= puVar3) {
              return (undefined4 *)0x0;
            }
            uVar9 = puVar3[1];
            if (uVar4 <= uVar9) goto LAB_0800edbc;
          }
          if (puVar6 == puVar11) {
            return (undefined4 *)0x0;
          }
          puVar10 = (undefined4 *)*puVar6;
          puVar1 = puVar3;
          puVar3 = puVar6;
          puVar6 = puVar10;
          if (puVar10 == (undefined4 *)0x0) {
            return (undefined4 *)0x0;
          }
        } while( true );
      }
    }
    return (undefined4 *)0x0;
  }
  while( true ) {
    if (puVar3 == (undefined4 *)0x0) {
      return (undefined4 *)0x0;
    }
    puVar6 = (undefined4 *)*puVar3;
    uVar9 = puVar3[1];
    if (uVar4 <= uVar9) break;
    if (puVar3 == puVar11) {
      return (undefined4 *)0x0;
    }
    puVar1 = puVar3;
    puVar3 = puVar6;
    if (puVar6 == (undefined4 *)0x0) {
      return (undefined4 *)0x0;
    }
  }
LAB_0800edbc:
  *puVar1 = puVar6;
  iVar8 = param_1[3];
  uVar2 = (uVar9 & 0x7fffffff) - uVar4;
  param_1[3] = iVar8 - uVar9;
  if (7 < uVar2) {
    puVar1 = (undefined4 *)((int)puVar3 + uVar4);
    puVar1[1] = uVar2;
    puVar3[1] = uVar4;
    iVar7 = puVar1[1];
    param_1[3] = iVar7 + (iVar8 - uVar9);
    do {
      if (param_1 == (undefined4 *)0x0) goto LAB_0800ee48;
      puVar10 = (undefined4 *)*param_1;
      puVar6 = param_1;
      param_1 = puVar10;
      if (puVar1 <= puVar10) break;
      if (puVar10 == (undefined4 *)0x0) goto LAB_0800ee48;
      param_1 = (undefined4 *)*puVar10;
      puVar6 = puVar10;
      if (puVar1 <= param_1) break;
      if (param_1 == (undefined4 *)0x0) goto LAB_0800ee48;
      puVar10 = (undefined4 *)*param_1;
      puVar6 = param_1;
      param_1 = puVar10;
      if (puVar1 <= puVar10) break;
      if (puVar10 == (undefined4 *)0x0) goto LAB_0800ee48;
      param_1 = (undefined4 *)*puVar10;
      puVar6 = puVar10;
    } while (param_1 < puVar1);
    if ((undefined4 *)((int)puVar6 + puVar6[1]) == puVar1) {
      iVar7 = iVar7 + puVar6[1];
      puVar6[1] = iVar7;
      puVar1 = puVar6;
    }
    puVar10 = param_1;
    if (((param_1[1] != 0) && ((undefined4 *)((int)puVar1 + iVar7) == param_1)) &&
       (puVar10 = puVar11, param_1 != puVar11)) {
      puVar10 = (undefined4 *)*param_1;
      puVar1[1] = param_1[1] + iVar7;
    }
    *puVar1 = puVar10;
    if (puVar6 != puVar1) {
      *puVar6 = puVar1;
    }
  }
LAB_0800ee48:
  *puVar3 = 0xdeadbeef;
  puVar3[1] = puVar3[1] | 0x80000000;
  return puVar3 + 2;
}



/* 0800ee94 */

/* WARNING: Removing unreachable block (ram,0x0800eec8) */
/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

int FUN_0800ee94(uint param_1)

{
  bool bVar1;
  uint *puVar2;
  uint *puVar3;
  uint uVar4;
  uint uVar5;
  uint *puVar6;
  uint uVar7;
  uint *puVar8;
  uint *puVar9;
  uint *puVar10;
  
  FUN_080119a0();
  if (_DAT_2001c320 == (uint *)0x0) {
    _DAT_2001c334 = (uint *)&DAT_2000c000;
    _DAT_2001c338 = 0;
    _DAT_2001c320 = (uint *)&DAT_20015ff8;
    _DAT_20015ff8 = 0;
    _DAT_20015ffc = 0;
    _DAT_2000c000 = &DAT_20015ff8;
    _DAT_2000c004 = 0x9ff8;
    _DAT_2001c324 = 0x9ff8;
    _DAT_2001c328 = 0x9ff8;
    DAT_2001c31c = 1;
  }
  if ((param_1 != 0) && ((DAT_2001c31c & (int)param_1 < 0) == 0)) {
    uVar5 = (param_1 & 0xfffffff8) + 0x10;
    if ((param_1 & 7) == 0) {
      uVar5 = param_1 + 8;
    }
    if (uVar5 - 1 < _DAT_2001c324) {
      uVar7 = _DAT_2001c334[1];
      puVar8 = (uint *)&DAT_2001c334;
      puVar10 = _DAT_2001c334;
      if (uVar7 < uVar5) {
        puVar2 = (uint *)*_DAT_2001c334;
        puVar9 = _DAT_2001c334;
        if (puVar2 == (uint *)0x0) {
          puVar8 = (uint *)&DAT_2001c334;
        }
        else {
          while (((uVar7 = puVar2[1], puVar8 = puVar9, puVar10 = puVar2, uVar7 < uVar5 &&
                  (puVar9 = (uint *)*puVar2, puVar9 != (uint *)0x0)) &&
                 (uVar7 = puVar9[1], puVar8 = puVar2, puVar10 = puVar9, uVar7 < uVar5))) {
            puVar2 = (uint *)*puVar9;
            if (((puVar2 == (uint *)0x0) ||
                (uVar7 = puVar2[1], puVar8 = puVar9, puVar10 = puVar2, uVar5 <= uVar7)) ||
               ((puVar9 = (uint *)*puVar2, puVar9 == (uint *)0x0 ||
                ((uVar7 = puVar9[1], puVar8 = puVar2, puVar10 = puVar9, uVar5 <= uVar7 ||
                 (puVar2 = (uint *)*puVar9, puVar2 == (uint *)0x0)))))) break;
          }
        }
      }
      if (puVar10 != _DAT_2001c320) {
        uVar4 = *puVar8;
        *puVar8 = *puVar10;
        if (0x10 < uVar7 - uVar5) {
          puVar8 = (uint *)((int)puVar10 + uVar5);
          if (((uint)puVar8 & 7) != 0) {
            bVar1 = (bool)isCurrentModePrivileged();
            if (bVar1) {
              setBasePriority(0x50);
            }
            InstructionSynchronizationBarrier(0xf);
            DataSynchronizationBarrier(0xf);
            do {
                    /* WARNING: Do nothing block with infinite loop */
            } while( true );
          }
          puVar9 = (uint *)&DAT_2001c334;
          puVar8[1] = uVar7 - uVar5;
          puVar10[1] = uVar5;
          do {
            puVar3 = (uint *)*puVar9;
            puVar2 = puVar3;
            puVar6 = puVar9;
            if (((puVar8 <= puVar3) ||
                (puVar9 = (uint *)*puVar3, puVar2 = puVar9, puVar6 = puVar3, puVar8 <= puVar9)) ||
               (puVar3 = (uint *)*puVar9, puVar2 = puVar3, puVar6 = puVar9, puVar8 <= puVar3))
            break;
            puVar9 = (uint *)*puVar3;
            puVar2 = puVar9;
            puVar6 = puVar3;
          } while (puVar9 < puVar8);
          uVar5 = puVar8[1];
          if ((uint *)((int)puVar6 + puVar6[1]) == puVar8) {
            uVar5 = uVar5 + puVar6[1];
            puVar6[1] = uVar5;
            puVar8 = puVar6;
          }
          puVar9 = puVar2;
          if (((uint *)((int)puVar8 + uVar5) == puVar2) &&
             (puVar9 = _DAT_2001c320, puVar2 != _DAT_2001c320)) {
            puVar9 = (uint *)*puVar2;
            puVar8[1] = puVar2[1] + uVar5;
          }
          *puVar8 = (uint)puVar9;
          if (puVar6 != puVar8) {
            *puVar6 = (uint)puVar8;
          }
        }
        uVar5 = puVar10[1];
        _DAT_2001c324 = _DAT_2001c324 - uVar5;
        if (_DAT_2001c324 < _DAT_2001c328) {
          _DAT_2001c328 = _DAT_2001c324;
        }
        if (DAT_2001c31c != 0) {
          uVar5 = uVar5 | 0x80000000;
        }
        *puVar10 = 0;
        puVar10[1] = uVar5;
        _DAT_2001c32c = _DAT_2001c32c + 1;
        FUN_08012fd0();
        if ((uVar4 & 7) == 0) {
          return uVar4 + 8;
        }
        bVar1 = (bool)isCurrentModePrivileged();
        if (bVar1) {
          setBasePriority(0x50);
        }
        InstructionSynchronizationBarrier(0xf);
        DataSynchronizationBarrier(0xf);
        do {
                    /* WARNING: Do nothing block with infinite loop */
        } while( true );
      }
    }
  }
  FUN_08012fd0();
  return 0;
}



/* 0800f07c */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

int FUN_0800f07c(void)

{
  if (_DAT_2001c268 != 0) {
    *(int *)(_DAT_2001c268 + 0x50) = *(int *)(_DAT_2001c268 + 0x50) + 1;
  }
  return _DAT_2001c268;
}



/* 0800f094 */

undefined4 FUN_0800f094(int param_1)

{
  bool bVar1;
  undefined4 uVar2;
  
  if (param_1 != 0) {
    FUN_08011360();
    uVar2 = *(undefined4 *)(param_1 + 0x1c);
    FUN_080113a8();
    return uVar2;
  }
  bVar1 = (bool)isCurrentModePrivileged();
  if (bVar1) {
    setBasePriority(0x50);
  }
  InstructionSynchronizationBarrier(0xf);
  DataSynchronizationBarrier(0xf);
  do {
                    /* WARNING: Do nothing block with infinite loop */
  } while( true );
}



/* 0800f104 */

void FUN_0800f104(int param_1)

{
  int iVar1;
  uint uVar2;
  int iVar3;
  uint in_fpscr;
  float fVar4;
  float fVar5;
  
  if (*(char *)(param_1 + 0x21) == '\x01') {
    uVar2 = *(uint *)(param_1 + 0x14) / 0x14;
    fVar4 = (float)VectorSignedToFloat(*(int *)(param_1 + 0xc) - *(int *)(param_1 + 8),
                                       (byte)(in_fpscr >> 0x16) & 3);
    fVar5 = (float)VectorUnsignedToFloat(uVar2,(byte)(in_fpscr >> 0x16) & 3);
    *(uint *)(param_1 + 0x1c) = uVar2;
    *(undefined2 *)(param_1 + 0x20) = 1;
    *(float *)(param_1 + 0x18) = fVar4 / fVar5;
  }
  else if ((*(byte *)(param_1 + 0x20) & 1) == 0) {
    *(int *)(param_1 + 0x10) = *(int *)(param_1 + 0xc) + *(int *)(param_1 + 4);
    return;
  }
  iVar1 = *(int *)(param_1 + 8);
  iVar3 = *(int *)(param_1 + 0x1c) + -1;
  *(int *)(param_1 + 0x1c) = iVar3;
  if (iVar3 != 0) {
    fVar4 = (float)VectorSignedToFloat(iVar3,(byte)(in_fpscr >> 0x16) & 3);
    iVar1 = iVar1 + (int)(*(float *)(param_1 + 0x18) * fVar4);
    *(int *)(param_1 + 0xc) = iVar1;
    *(int *)(param_1 + 0x10) = iVar1 + *(int *)(param_1 + 4);
    return;
  }
  *(int *)(param_1 + 0xc) = iVar1;
  *(undefined1 *)(param_1 + 0x20) = 0;
  *(int *)(param_1 + 0x10) = iVar1 + *(int *)(param_1 + 4);
  return;
}



/* 0800f2a0 */

int FUN_0800f2a0(int param_1,uint param_2,undefined4 param_3)

{
  *(undefined4 *)(param_1 + -4) = 0x1000000;
  *(uint *)(param_1 + -8) = param_2 & 0xfffffffe;
  *(undefined4 *)(param_1 + -0xc) = 0x800e8ed;
  *(undefined4 *)(param_1 + -0x24) = 0xfffffffd;
  *(undefined4 *)(param_1 + -0x20) = param_3;
  return param_1 + -0x44;
}



/* 0800f2c4 */

uint FUN_0800f2c4(char *param_1,undefined4 *param_2)

{
  uint uVar1;
  ushort uVar2;
  ushort uVar3;
  ushort uVar4;
  ushort uVar5;
  
  if (*param_1 != '\x0f') {
    return 0xffffffff;
  }
  if (param_1[0x18] != '\0') {
    return 0xfffffffe;
  }
  *param_2 = 3;
  uVar4 = (ushort)(byte)param_1[1] | ((byte)param_1[2] & 7) << 8;
  *(ushort *)(param_2 + 1) = uVar4;
  uVar5 = (ushort)((byte)param_1[2] >> 3) | ((byte)param_1[3] & 0x3f) << 5;
  *(ushort *)((int)param_2 + 6) = uVar5;
  uVar2 = (ushort)(byte)param_1[4] << 2 | (ushort)((byte)param_1[3] >> 6) |
          ((byte)param_1[5] & 1) << 10;
  *(ushort *)(param_2 + 2) = uVar2;
  uVar3 = (ushort)((byte)param_1[5] >> 1) | ((byte)param_1[6] & 0xf) << 7;
  *(ushort *)((int)param_2 + 10) = uVar3;
  *(ushort *)(param_2 + 3) = (ushort)((byte)param_1[6] >> 4) | ((byte)param_1[7] & 0x7f) << 4;
  *(ushort *)((int)param_2 + 0xe) =
       (ushort)(byte)param_1[8] << 1 | (ushort)((byte)param_1[7] >> 7) | ((byte)param_1[9] & 3) << 9
  ;
  *(ushort *)(param_2 + 4) = (ushort)((byte)param_1[9] >> 2) | ((byte)param_1[10] & 0x1f) << 6;
  *(ushort *)((int)param_2 + 0x12) =
       (ushort)(byte)param_1[0xb] << 3 | (ushort)((byte)param_1[10] >> 5);
  *(ushort *)(param_2 + 5) = (ushort)(byte)param_1[0xc] | ((byte)param_1[0xd] & 7) << 8;
  *(ushort *)((int)param_2 + 0x16) =
       (ushort)((byte)param_1[0xd] >> 3) | ((byte)param_1[0xe] & 0x3f) << 5;
  *(ushort *)(param_2 + 6) =
       (ushort)(byte)param_1[0xf] << 2 | (ushort)((byte)param_1[0xe] >> 6) |
       ((byte)param_1[0x10] & 1) << 10;
  *(ushort *)((int)param_2 + 0x1a) =
       (ushort)((byte)param_1[0x10] >> 1) | ((byte)param_1[0x11] & 0xf) << 7;
  *(ushort *)(param_2 + 7) = (ushort)((byte)param_1[0x11] >> 4) | ((byte)param_1[0x12] & 0x7f) << 4;
  *(ushort *)((int)param_2 + 0x1e) =
       (ushort)(byte)param_1[0x13] << 1 | (ushort)((byte)param_1[0x12] >> 7) |
       ((byte)param_1[0x14] & 3) << 9;
  *(ushort *)(param_2 + 8) = (ushort)((byte)param_1[0x14] >> 2) | ((byte)param_1[0x15] & 0x1f) << 6;
  *(ushort *)((int)param_2 + 0x22) =
       (ushort)(byte)param_1[0x16] << 3 | (ushort)((byte)param_1[0x15] >> 5);
  *(byte *)(param_2 + 9) = (byte)param_1[0x17] >> 7;
  *(byte *)((int)param_2 + 0x25) = (byte)(((uint)(byte)param_1[0x17] << 0x19) >> 0x1f);
  *(byte *)((int)param_2 + 0x26) = (byte)(((uint)(byte)param_1[0x17] << 0x1a) >> 0x1f);
  *(byte *)((int)param_2 + 0x27) = (byte)(((uint)(byte)param_1[0x17] << 0x1b) >> 0x1f);
  if (uVar4 != 0x3e0 || uVar5 != 0x3e0) {
    return 0;
  }
  if (uVar2 == 0x20) {
    uVar1 = (uint)(uVar3 == 0x3e0);
    if (uVar3 == 0x3e0) {
      *(undefined1 *)((int)param_2 + 0x26) = 1;
      uVar1 = 0;
    }
    return uVar1;
  }
  return 0;
}



/* 0800f420 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_0800f420(undefined4 param_1,uint param_2)

{
  uint uVar1;
  
  uVar1 = _DAT_2001c3f8;
  _DAT_2001c3f8 = _DAT_2001c3f8 ^ 1;
  if (param_2 < 0x20) {
    FUN_08004b64(&DAT_2001e270);
  }
  FUN_08004980(&DAT_2001e270,*(undefined4 *)(&DAT_2001c404 + _DAT_2001c3f8 * 4),0x20);
  FUN_0800cb9c(_DAT_2001c400,*(undefined4 *)(&DAT_2001c404 + uVar1 * 4),param_2);
  uVar1 = FUN_0800c874(_DAT_2001c400);
  if (0x18 < uVar1) {
    FUN_0800d7a8(_DAT_2001c20c);
    return;
  }
  return;
}



/* 0800f6bc */

void FUN_0800f6bc(int param_1,char param_2,char param_3)

{
  undefined2 local_15;
  char local_13;
  undefined2 local_12;
  char local_10;
  char local_f;
  undefined1 local_e;
  
  local_15 = 0x5555;
  local_f = -0x24 - (param_2 + param_3);
  local_12 = 0x1f04;
  local_e = 0;
  local_13 = param_2;
  local_10 = param_3;
  (**(code **)(param_1 + 0x34))(param_1,&local_15,1);
  return;
}



/* 0800f6f8 */

undefined4 FUN_0800f6f8(int param_1,char param_2,undefined2 *param_3)

{
  int iVar1;
  undefined2 local_1d;
  char local_1b;
  undefined2 local_1a;
  char local_18;
  undefined1 local_17;
  
  local_1d = 0x5555;
  local_1a = 0x1503;
  local_18 = -0x19 - param_2;
  local_17 = 0;
  local_1b = param_2;
  iVar1 = (**(code **)(param_1 + 0x34))(param_1,&local_1d,0);
  if (iVar1 != 0) {
    return 0xffffffff;
  }
  *param_3 = *(undefined2 *)(param_1 + 9);
  param_3[1] = *(undefined2 *)(param_1 + 0xb);
  return 0;
}



/* 0800f750 */

undefined4 FUN_0800f750(int param_1,char param_2,undefined1 *param_3)

{
  int iVar1;
  undefined2 local_1d;
  char local_1b;
  undefined2 local_1a;
  char local_18;
  undefined1 local_17;
  
  local_1d = 0x5555;
  local_1a = 0x1303;
  local_18 = -0x17 - param_2;
  local_17 = 0;
  local_1b = param_2;
  iVar1 = (**(code **)(param_1 + 0x34))(param_1,&local_1d,0);
  if (iVar1 != 0) {
    return 0xffffffff;
  }
  *param_3 = *(undefined1 *)(param_1 + 9);
  return 0;
}



/* 0800f7a0 */

undefined4 FUN_0800f7a0(int param_1,char param_2,undefined1 *param_3)

{
  int iVar1;
  undefined2 local_1d;
  char local_1b;
  undefined2 local_1a;
  char local_18;
  undefined1 local_17;
  
  local_1d = 0x5555;
  local_1a = 0xe03;
  local_18 = -0x12 - param_2;
  local_17 = 0;
  local_1b = param_2;
  iVar1 = (**(code **)(param_1 + 0x34))(param_1,&local_1d,0);
  if (iVar1 != 0) {
    return 0xffffffff;
  }
  *param_3 = *(undefined1 *)(param_1 + 9);
  return 0;
}



/* 0800f7f0 */

undefined4 FUN_0800f7f0(int param_1,char param_2,undefined1 *param_3)

{
  int iVar1;
  undefined2 local_1d;
  char local_1b;
  undefined2 local_1a;
  char local_18;
  undefined1 local_17;
  
  local_1d = 0x5555;
  local_1a = 0x2003;
  local_18 = -0x24 - param_2;
  local_17 = 0;
  local_1b = param_2;
  iVar1 = (**(code **)(param_1 + 0x34))(param_1,&local_1d,0);
  if (iVar1 != 0) {
    return 0xffffffff;
  }
  *param_3 = *(undefined1 *)(param_1 + 9);
  return 0;
}



/* 0800f840 */

undefined4 FUN_0800f840(int param_1,char param_2,undefined2 *param_3)

{
  int iVar1;
  undefined2 local_1d;
  char local_1b;
  undefined2 local_1a;
  char local_18;
  undefined1 local_17;
  
  local_1d = 0x5555;
  local_1a = 0x1c03;
  local_18 = -0x20 - param_2;
  local_17 = 0;
  local_1b = param_2;
  iVar1 = (**(code **)(param_1 + 0x34))(param_1,&local_1d,0);
  if (iVar1 != 0) {
    return 0xffffffff;
  }
  *param_3 = *(undefined2 *)(param_1 + 9);
  return 0;
}



/* 0800f890 */

undefined4 FUN_0800f890(int param_1,char param_2,undefined1 *param_3)

{
  int iVar1;
  undefined2 local_1d;
  char local_1b;
  undefined2 local_1a;
  char local_18;
  undefined1 local_17;
  
  local_1d = 0x5555;
  local_1a = 0x1a03;
  local_18 = -0x1e - param_2;
  local_17 = 0;
  local_1b = param_2;
  iVar1 = (**(code **)(param_1 + 0x34))(param_1,&local_1d,0);
  if (iVar1 != 0) {
    return 0xffffffff;
  }
  *param_3 = *(undefined1 *)(param_1 + 9);
  return 0;
}



/* 0800f8e0 */

undefined4 FUN_0800f8e0(int param_1,char param_2,undefined1 *param_3)

{
  int iVar1;
  undefined2 local_1d;
  char local_1b;
  undefined2 local_1a;
  char local_18;
  undefined1 local_17;
  
  local_1d = 0x5555;
  local_1a = 0x1903;
  local_18 = -0x1d - param_2;
  local_17 = 0;
  local_1b = param_2;
  iVar1 = (**(code **)(param_1 + 0x34))(param_1,&local_1d,0);
  if (iVar1 != 0) {
    return 0xffffffff;
  }
  *param_3 = *(undefined1 *)(param_1 + 9);
  return 0;
}



/* 0800f930 */

undefined4 FUN_0800f930(int param_1,char param_2,undefined2 *param_3)

{
  int iVar1;
  undefined2 local_1d;
  char local_1b;
  undefined2 local_1a;
  char local_18;
  undefined1 local_17;
  
  local_1d = 0x5555;
  local_1a = 0x1b03;
  local_18 = -0x1f - param_2;
  local_17 = 0;
  local_1b = param_2;
  iVar1 = (**(code **)(param_1 + 0x34))(param_1,&local_1d,0);
  if (iVar1 != 0) {
    return 0xffffffff;
  }
  *param_3 = *(undefined2 *)(param_1 + 9);
  return 0;
}



/* 0800f980 */

undefined4 FUN_0800f980(int param_1,char param_2,undefined2 *param_3)

{
  int iVar1;
  undefined2 local_1d;
  char local_1b;
  undefined2 local_1a;
  char local_18;
  undefined1 local_17;
  
  local_1d = 0x5555;
  local_1a = 0x1703;
  local_18 = -0x1b - param_2;
  local_17 = 0;
  local_1b = param_2;
  iVar1 = (**(code **)(param_1 + 0x34))(param_1,&local_1d,0);
  if (iVar1 != 0) {
    return 0xffffffff;
  }
  *param_3 = *(undefined2 *)(param_1 + 9);
  param_3[1] = *(undefined2 *)(param_1 + 0xb);
  return 0;
}



/* 0800f9d8 */

void FUN_0800f9d8(int param_1,char param_2)

{
  undefined2 local_15;
  char local_13;
  undefined2 local_12;
  char local_10;
  undefined1 local_f;
  
  local_15 = 0x5555;
  local_12 = 0x1203;
  local_10 = -0x16 - param_2;
  local_f = 0;
  local_13 = param_2;
  (**(code **)(param_1 + 0x34))(param_1,&local_15,1);
  return;
}



/* 0800fa10 */

void FUN_0800fa10(int param_1,char param_2,uint param_3,uint param_4)

{
  uint uVar1;
  uint uVar2;
  undefined2 local_15;
  char local_13;
  undefined2 local_12;
  char local_10;
  char local_f;
  char local_e;
  char local_d;
  char local_c;
  undefined1 local_b;
  
  local_15 = 0x5555;
  if (999 < param_3) {
    param_3 = 1000;
  }
  uVar1 = 1000;
  if (param_4 < 1000) {
    uVar1 = param_4;
  }
  uVar2 = uVar1;
  if (param_4 < param_3) {
    uVar2 = param_3;
    param_3 = uVar1;
  }
  local_10 = (char)param_3;
  local_f = (char)(param_3 >> 8);
  local_d = (char)(uVar2 >> 8);
  local_e = (char)uVar2;
  local_12 = 0x1407;
  local_c = -0x1c - (param_2 + local_10 + local_f + local_e + local_d);
  local_b = 0;
  local_13 = param_2;
  (**(code **)(param_1 + 0x34))(param_1,&local_15,1);
  return;
}



/* 0800fa88 */

void FUN_0800fa88(int param_1,char param_2,char param_3)

{
  undefined2 local_15;
  char local_13;
  undefined2 local_12;
  char local_10;
  char local_f;
  undefined1 local_e;
  
  local_15 = 0x5555;
  local_f = -0x16 - (param_2 + param_3);
  local_12 = 0x1104;
  local_e = 0;
  local_13 = param_2;
  local_10 = param_3;
  (**(code **)(param_1 + 0x34))(param_1,&local_15,1);
  return;
}



/* 0800fac4 */

void FUN_0800fac4(int param_1,char param_2,char param_3)

{
  undefined2 local_15;
  char local_13;
  undefined2 local_12;
  char local_10;
  char local_f;
  undefined1 local_e;
  
  local_15 = 0x5555;
  local_f = -0x12 - (param_2 + param_3);
  local_12 = 0xd04;
  local_e = 0;
  local_13 = param_2;
  local_10 = param_3;
  (**(code **)(param_1 + 0x34))(param_1,&local_15,1);
  return;
}



/* 0800fb00 */

void FUN_0800fb00(int param_1,char param_2,int param_3,undefined4 param_4)

{
  undefined2 local_15;
  char local_13;
  undefined2 local_12;
  char local_10;
  char local_f;
  char local_e;
  char local_d;
  char local_c;
  undefined1 local_b;
  
  if (999 < param_3) {
    param_3 = 1000;
  }
  local_10 = (char)param_3;
  local_f = (char)((uint)param_3 >> 8);
  local_e = (char)param_4;
  local_15 = 0x5555;
  local_d = (char)((uint)param_4 >> 8);
  local_c = -9 - (param_2 + local_10 + local_f + local_e + local_d);
  local_b = 0;
  local_12 = 0x107;
  local_13 = param_2;
  (**(code **)(param_1 + 0x34))(param_1,&local_15,1);
  return;
}



/* 0800fb64 */

void FUN_0800fb64(int param_1,char param_2,uint param_3)

{
  undefined2 local_15;
  char local_13;
  undefined2 local_12;
  char local_10;
  char local_f;
  undefined1 local_e;
  
  local_15 = 0x5555;
  if (99 < param_3) {
    param_3 = 100;
  }
  local_10 = (char)param_3;
  local_f = -0x1d - (param_2 + local_10);
  local_12 = 0x1804;
  local_e = 0;
  local_13 = param_2;
  (**(code **)(param_1 + 0x34))(param_1,&local_15,1);
  return;
}



/* 0800fba8 */

void FUN_0800fba8(int param_1,char param_2,uint param_3,uint param_4)

{
  uint uVar1;
  uint uVar2;
  uint uVar3;
  undefined2 local_15;
  char local_13;
  undefined2 local_12;
  char local_10;
  char local_f;
  char local_e;
  char local_d;
  char local_c;
  undefined1 local_b;
  
  local_15 = 0x5555;
  uVar2 = 0x1194;
  if (0x1194 < param_3) {
    uVar2 = param_3;
  }
  uVar1 = 14000;
  if (param_4 < 14000) {
    uVar1 = param_4;
  }
  uVar3 = uVar1;
  if (uVar2 < uVar1) {
    uVar3 = uVar2;
  }
  local_10 = (char)uVar3;
  local_f = (char)(uVar3 >> 8);
  if (uVar1 < uVar2) {
    uVar1 = uVar2;
  }
  local_e = (char)uVar1;
  local_d = (char)(uVar1 >> 8);
  local_c = -0x1e - (param_2 + local_10 + local_f + local_e + local_d);
  local_12 = 0x1607;
  local_b = 0;
  local_13 = param_2;
  (**(code **)(param_1 + 0x34))(param_1,&local_15,1);
  return;
}



/* 0800fc20 */

void FUN_0800fc20(int param_1,char param_2)

{
  undefined2 local_15;
  char local_13;
  undefined2 local_12;
  char local_10;
  undefined1 local_f;
  
  local_15 = 0x5555;
  local_12 = 0xc03;
  local_10 = -0x10 - param_2;
  local_f = 0;
  local_13 = param_2;
  (**(code **)(param_1 + 0x34))(param_1,&local_15,1);
  return;
}



/* 0800fc58 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined4 FUN_0800fc58(undefined4 *param_1,undefined4 *param_2,undefined1 param_3)

{
  undefined4 *puVar1;
  undefined4 uVar2;
  int iVar3;
  undefined4 uVar4;
  undefined4 uVar5;
  
  FUN_08001f84(0x40021000,0x100,1);
  FUN_08001f84(0x40021000,0x80,0);
  *(undefined1 *)(param_1 + 9) = *(undefined1 *)(param_2 + 3);
  uVar2 = *param_2;
  uVar4 = param_2[2];
  uVar5 = param_2[1];
  *(undefined1 *)(param_1 + 0xb) = param_3;
  param_1[6] = uVar2;
  puVar1 = _DAT_2001e2f0;
  *(undefined1 *)(param_1 + 4) = 0;
  param_1[10] = 0;
  param_1[5] = 0;
  *param_1 = 0;
  param_1[1] = 0;
  param_1[2] = 0;
  param_1[3] = 0;
  param_1[8] = uVar4;
  param_1[7] = uVar5;
  *puVar1 = 0xffffffdf;
  *puVar1 = 0xffffff7f;
  *puVar1 = 0xffffffbf;
  puVar1[3] = puVar1[3] | 0x80;
  puVar1[3] = puVar1[3] | 0x40;
  puVar1[3] = puVar1[3] | 0x20;
  iVar3 = FUN_0800d684(_DAT_2001c218,param_1[0xc]);
  puVar1 = _DAT_2001e2f0;
  _DAT_2001e2f0[3] = _DAT_2001e2f0[3] & 0xffffff7f;
  puVar1[3] = puVar1[3] & 0xffffffbf;
  uVar2 = 0;
  if (iVar3 != 0) {
    uVar2 = 0xffffffff;
  }
  puVar1[3] = puVar1[3] & 0xffffffdf;
  *puVar1 = 0xffffffdf;
  *puVar1 = 0xffffff7f;
  *puVar1 = 0xffffffbf;
  FUN_08001f84(0x40021000,0x100,1);
  FUN_08001f84(0x40021000,0x80,1);
  return uVar2;
}



/* 0800fd3c */

undefined4 FUN_0800fd3c(undefined4 param_1)

{
  undefined4 local_c;
  
  local_c = param_1;
  FUN_08006ccc(0,&local_c,1);
  return local_c;
}



/* 0800fd54 */

undefined4 FUN_0800fd54(undefined4 param_1)

{
  undefined4 local_c;
  
  local_c = param_1;
  FUN_08006ccc(0,&local_c,1);
  return local_c;
}



/* 0800fd6c */

void FUN_0800fd6c(void)

{
  return;
}



/* 0800fd70 */

void FUN_0800fd70(int *param_1)

{
  FUN_08000744(param_1[0xd],(uint)*(byte *)(param_1 + 0xe) * (uint)*(byte *)(*param_1 + 0x10) * 8);
  return;
}



/* 0800fd88 */

void FUN_0800fd88(int param_1,uint param_2,uint param_3,uint param_4,uint param_5)

{
  uint uVar1;
  short sVar2;
  uint uVar3;
  uint uVar4;
  ushort uVar5;
  uint uVar6;
  uint uVar7;
  undefined4 uVar8;
  
  if (param_4 == 0) {
    return;
  }
  if (*(char *)(param_1 + 0x8c) == '\0') {
    return;
  }
  if (param_4 < 2) {
LAB_0800fdb8:
    if ((param_5 & 1) != 0) {
LAB_0800fe24:
      if (param_2 < *(ushort *)(param_1 + 0x48)) {
        return;
      }
      if (*(ushort *)(param_1 + 0x4a) <= param_2) {
        return;
      }
      uVar6 = (uint)*(ushort *)(param_1 + 0x4c);
      uVar7 = (uint)*(ushort *)(param_1 + 0x4e);
      param_4 = param_4 + (param_3 & 0xffff);
      uVar4 = param_4 & 0xffff;
      uVar5 = *(ushort *)(param_1 + 0x4c);
      if ((param_3 & 0xffff) < uVar7) {
        uVar5 = (ushort)param_3;
      }
      if (uVar4 == param_4) {
        uVar5 = (ushort)param_3;
      }
      uVar1 = (uint)uVar5;
      uVar3 = param_4;
      if ((param_3 & 0xffff) < uVar7) {
        uVar3 = uVar7 - 1;
      }
      if (uVar4 == param_4) {
        uVar3 = uVar4;
      }
      if (uVar7 <= uVar1) {
        return;
      }
      if ((uVar3 & 0xffff) <= uVar6) {
        return;
      }
      param_3 = uVar6;
      if (uVar6 < uVar1) {
        param_3 = uVar1;
      }
      uVar5 = *(ushort *)(param_1 + 0x4e);
      if ((uVar3 & 0xffff) < uVar7) {
        uVar5 = (ushort)uVar3;
      }
      sVar2 = uVar5 - (short)param_3;
      uVar8 = 1;
      goto LAB_0800fe84;
    }
  }
  else {
    if (param_5 == 3) {
      param_3 = (param_3 - param_4) + 1;
      goto LAB_0800fe24;
    }
    if (param_5 != 2) goto LAB_0800fdb8;
    param_2 = (param_2 - param_4) + 1;
  }
  if (param_3 < *(ushort *)(param_1 + 0x4c)) {
    return;
  }
  if (*(ushort *)(param_1 + 0x4e) <= param_3) {
    return;
  }
  uVar6 = (uint)*(ushort *)(param_1 + 0x48);
  uVar7 = (uint)*(ushort *)(param_1 + 0x4a);
  param_4 = param_4 + (param_2 & 0xffff);
  uVar4 = param_4 & 0xffff;
  uVar5 = *(ushort *)(param_1 + 0x48);
  if ((param_2 & 0xffff) < uVar7) {
    uVar5 = (ushort)param_2;
  }
  if (uVar4 == param_4) {
    uVar5 = (ushort)param_2;
  }
  uVar1 = (uint)uVar5;
  uVar3 = param_4;
  if ((param_2 & 0xffff) < uVar7) {
    uVar3 = uVar7 - 1;
  }
  if (uVar4 == param_4) {
    uVar3 = uVar4;
  }
  if (uVar7 <= uVar1) {
    return;
  }
  if ((uVar3 & 0xffff) <= uVar6) {
    return;
  }
  param_2 = uVar6;
  if (uVar6 < uVar1) {
    param_2 = uVar1;
  }
  uVar5 = *(ushort *)(param_1 + 0x4a);
  if ((uVar3 & 0xffff) < uVar7) {
    uVar5 = (ushort)uVar3;
  }
  sVar2 = uVar5 - (short)param_2;
  uVar8 = 0;
LAB_0800fe84:
  (**(code **)(*(int *)(param_1 + 0x30) + 8))(param_1,param_2,param_3,sVar2,uVar8);
  return;
}



/* 0800fe94 */

void FUN_0800fe94(int param_1)

{
  *(undefined1 **)(param_1 + 4) = &LAB_08010cb0_1;
  FUN_0801013c();
  return;
}



/* 0800fea4 */

bool FUN_0800fea4(int param_1,uint param_2,uint param_3,uint param_4,uint param_5)

{
  uint uVar1;
  bool bVar2;
  bool bVar3;
  
  uVar1 = (uint)*(ushort *)(param_1 + 0x4c);
  if (param_3 < *(ushort *)(param_1 + 0x4e)) {
    bVar3 = param_5 <= param_3;
    bVar2 = param_3 == param_5;
    if (!bVar3 || bVar2) {
      bVar3 = uVar1 <= param_5;
      bVar2 = param_5 == uVar1;
    }
    if (!bVar3 || bVar2) {
      return false;
    }
  }
  else {
    bVar3 = param_5 <= param_3;
    bVar2 = param_3 == param_5;
    if (bVar3 && !bVar2) {
      bVar3 = uVar1 <= param_5;
      bVar2 = param_5 == uVar1;
    }
    if (!bVar3 || bVar2) {
      return false;
    }
  }
  if (param_2 < *(ushort *)(param_1 + 0x4a)) {
    return param_4 < param_2 || *(ushort *)(param_1 + 0x48) < param_4;
  }
  return *(ushort *)(param_1 + 0x48) < param_4 && param_4 < param_2;
}



/* 0800ff10 */

void FUN_0800ff10(int param_1)

{
  FUN_08010b0c();
                    /* WARNING: Could not recover jumptable at 0x08010c66. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (**(code **)(param_1 + 8))(param_1,0x10,0,0);
  return;
}



/* 0800ff24 */

void FUN_0800ff24(int param_1,undefined1 *param_2)

{
  char cVar1;
  char cVar2;
  char cVar3;
  char cVar4;
  char cVar5;
  char cVar6;
  undefined2 uVar7;
  int iVar8;
  
  if (*(undefined1 **)(param_1 + 0x58) != param_2) {
    *(undefined1 **)(param_1 + 0x58) = param_2;
    *(undefined1 *)(param_1 + 0x74) = *param_2;
    *(undefined1 *)(param_1 + 0x75) = param_2[1];
    *(undefined1 *)(param_1 + 0x76) = param_2[2];
    *(undefined1 *)(param_1 + 0x77) = param_2[3];
    *(undefined1 *)(param_1 + 0x78) = param_2[4];
    *(undefined1 *)(param_1 + 0x79) = param_2[5];
    *(undefined1 *)(param_1 + 0x7a) = param_2[6];
    *(undefined1 *)(param_1 + 0x7b) = param_2[7];
    *(undefined1 *)(param_1 + 0x7c) = param_2[8];
    *(undefined1 *)(param_1 + 0x7d) = param_2[9];
    cVar1 = param_2[10];
    *(char *)(param_1 + 0x7e) = cVar1;
    *(undefined1 *)(param_1 + 0x7f) = param_2[0xb];
    cVar2 = param_2[0xc];
    *(char *)(param_1 + 0x80) = cVar2;
    cVar3 = param_2[0xd];
    *(char *)(param_1 + 0x81) = cVar3;
    cVar4 = param_2[0xe];
    *(char *)(param_1 + 0x82) = cVar4;
    cVar5 = param_2[0xf];
    *(char *)(param_1 + 0x83) = cVar5;
    cVar6 = param_2[0x10];
    *(char *)(param_1 + 0x84) = cVar6;
    uVar7 = FUN_08010820(param_2,0x11);
    *(undefined2 *)(param_1 + 0x86) = uVar7;
    uVar7 = FUN_08010820(param_2,0x13);
    *(undefined2 *)(param_1 + 0x88) = uVar7;
    uVar7 = FUN_08010820(param_2,0x15);
    *(undefined2 *)(param_1 + 0x8a) = uVar7;
    *(char *)(param_1 + 0x8e) = cVar3;
    *(char *)(param_1 + 0x8f) = cVar4;
    if (*(char *)(param_1 + 0x8d) != '\0') {
      if (*(char *)(param_1 + 0x8d) == '\x01') {
        if ((int)cVar3 < (int)cVar5) {
          *(char *)(param_1 + 0x8e) = cVar5;
        }
        if ((int)cVar6 < (int)cVar4) {
          *(char *)(param_1 + 0x8f) = cVar6;
        }
      }
      else {
        iVar8 = (int)cVar2 + (int)cVar1;
        if (cVar3 < iVar8) {
          *(char *)(param_1 + 0x8e) = (char)iVar8;
        }
        if ((int)cVar2 < (int)cVar4) {
          *(char *)(param_1 + 0x8f) = cVar2;
          return;
        }
      }
    }
  }
  return;
}



/* 08010010 */

void FUN_08010010(int param_1,undefined1 param_2)

{
  *(undefined1 *)(param_1 + 0x70) = param_2;
  return;
}



/* 08010018 */

void FUN_08010018(int param_1,undefined1 param_2)

{
  *(undefined1 *)(param_1 + 0x6d) = param_2;
  return;
}



/* 08010020 */

void FUN_08010020(int param_1)

{
  *(undefined1 **)(param_1 + 0x5c) = &LAB_0801022c_1;
  return;
}



/* 0801002c */

void FUN_0801002c(int param_1,undefined4 param_2,undefined1 param_3,undefined4 param_4,
                 undefined4 *param_5)

{
  code *pcVar1;
  
  *(undefined1 *)(param_1 + 0x38) = param_3;
  *(undefined2 *)(param_1 + 0x92) = 0x101;
  pcVar1 = (code *)*param_5;
  *(undefined4 *)(param_1 + 0x2c) = param_4;
  *(undefined4 **)(param_1 + 0x30) = param_5;
  *(undefined4 *)(param_1 + 0x58) = 0;
  *(undefined1 *)(param_1 + 0x39) = 0;
  *(undefined1 *)(param_1 + 0x6d) = 0;
  *(undefined1 *)(param_1 + 0x91) = 0;
  *(undefined1 *)(param_1 + 0x8d) = 0;
  *(undefined4 *)(param_1 + 0x34) = param_2;
  (*pcVar1)(param_1);
  *(undefined4 *)(param_1 + 0x50) = 0xffff0000;
  *(undefined4 *)(param_1 + 0x54) = 0xffff0000;
  (**(code **)(*(int *)(param_1 + 0x30) + 4))(param_1);
  FUN_08010020(param_1);
  *(undefined1 *)(param_1 + 0x70) = 0;
  return;
}



/* 0801007c */

void FUN_0801007c(undefined4 param_1,undefined4 param_2,undefined4 param_3,undefined4 param_4)

{
  undefined4 uVar1;
  undefined1 local_11;
  
  FUN_08010c74(param_1,&LAB_08011170_1,&LAB_08010eb4_1,param_3,param_4);
  uVar1 = FUN_08010afc(&local_11);
  FUN_0801002c(param_1,uVar1,local_11,0x8010879,param_2);
  return;
}



/* 080100c0 */

short FUN_080100c0(short param_1,short param_2,short param_3,int param_4)

{
  if (param_4 == 2) {
    return param_1 - param_2;
  }
  if (param_4 != 1) {
    if (param_4 == 0) {
      param_3 = param_2;
    }
    return param_1 + param_3;
  }
  return param_1 - param_3;
}



/* 080100e4 */

short FUN_080100e4(short param_1,short param_2,short param_3,int param_4)

{
  if (param_4 == 2) {
    return param_1 - param_3;
  }
  if (param_4 != 1) {
    if (param_4 != 0) {
      param_3 = -param_2;
    }
    return param_1 + param_3;
  }
  return param_1 + param_2;
}



/* 08010108 */

void FUN_08010108(int param_1,undefined4 param_2,short param_3,undefined4 param_4,undefined4 param_5
                 )

{
  (**(code **)(param_1 + 0x2c))
            (param_1,param_2,param_3 - *(short *)(param_1 + 0x3e),param_4,param_5);
  return;
}



/* 08010128 */

void FUN_08010128(void)

{
  FUN_08010108();
  return;
}



/* 0801013c */

short FUN_0801013c(int param_1,short param_2,short param_3,undefined1 *param_4)

{
  byte bVar1;
  short sVar2;
  short sVar3;
  uint uVar4;
  int iVar5;
  short sVar6;
  
  FUN_0801123c();
  uVar4 = (**(code **)(param_1 + 4))(param_1,*param_4);
  if (uVar4 == 0xffff) {
    sVar6 = 0;
  }
  else {
    sVar6 = 0;
    do {
      param_4 = param_4 + 1;
      if ((uVar4 & 0xffff) == 0xfffe) goto LAB_08010172;
      sVar3 = param_2;
      sVar2 = param_3;
      switch(*(undefined1 *)(param_1 + 0x70)) {
      case 0:
        sVar2 = (**(code **)(param_1 + 0x5c))(param_1);
        sVar2 = sVar2 + param_3;
        break;
      case 1:
        sVar3 = (**(code **)(param_1 + 0x5c))(param_1);
        sVar3 = -sVar3;
        goto LAB_080101cc;
      case 2:
        sVar2 = (**(code **)(param_1 + 0x5c))(param_1);
        sVar2 = param_3 - sVar2;
        break;
      case 3:
        sVar3 = (**(code **)(param_1 + 0x5c))(param_1);
LAB_080101cc:
        sVar3 = sVar3 + param_2;
      }
      *(short *)(param_1 + 100) = sVar3;
      *(short *)(param_1 + 0x66) = sVar2;
      iVar5 = FUN_08010754(param_1,uVar4 & 0xffff);
      if (iVar5 == 0) {
        sVar3 = 0;
        bVar1 = *(byte *)(param_1 + 0x70);
      }
      else {
        sVar3 = FUN_08010230(param_1,iVar5);
        bVar1 = *(byte *)(param_1 + 0x70);
      }
      if (bVar1 < 4) {
        switch(bVar1) {
        case 0:
          param_2 = param_2 + sVar3;
          break;
        case 1:
          param_3 = param_3 + sVar3;
          break;
        case 2:
          param_2 = param_2 - sVar3;
          break;
        case 3:
          param_3 = param_3 - sVar3;
        }
      }
      sVar6 = sVar6 + sVar3;
LAB_08010172:
      uVar4 = (**(code **)(param_1 + 4))(param_1,*param_4);
    } while (uVar4 != 0xffff);
  }
  return sVar6;
}



/* 08010230 */

int FUN_08010230(int param_1,byte *param_2)

{
  byte bVar1;
  undefined1 uVar2;
  undefined2 uVar3;
  char cVar4;
  short sVar5;
  short sVar6;
  uint uVar7;
  undefined4 uVar8;
  undefined4 uVar9;
  short sVar10;
  uint uVar11;
  short sVar12;
  byte bVar13;
  byte *pbVar14;
  uint uVar15;
  byte bVar16;
  short sVar17;
  uint uVar18;
  uint uVar19;
  byte bVar20;
  byte *pbVar21;
  int iVar22;
  uint uVar23;
  int iVar24;
  int iVar25;
  uint uVar26;
  uint uVar27;
  byte bVar28;
  
  *(byte **)(param_1 + 0x60) = param_2;
  *(undefined1 *)(param_1 + 0x6c) = 0;
  uVar7 = (uint)*(byte *)(param_1 + 0x78);
  bVar1 = *param_2;
  uVar11 = uVar7;
  if (7 < uVar7) {
    param_2 = param_2 + 1;
    *(byte **)(param_1 + 0x60) = param_2;
    uVar11 = uVar7 - 8;
  }
  bVar1 = bVar1 & ~(byte)(-1 << uVar7);
  *(char *)(param_1 + 0x6c) = (char)uVar11;
  *(byte *)(param_1 + 0x6a) = bVar1;
  uVar7 = *(byte *)(param_1 + 0x79) + uVar11;
  bVar20 = *param_2 >> (uVar11 & 0xff);
  pbVar14 = param_2;
  if (7 < (uVar7 & 0xff)) {
    pbVar14 = param_2 + 1;
    *(byte **)(param_1 + 0x60) = pbVar14;
    bVar20 = bVar20 | param_2[1] << (8 - uVar11 & 0xff);
    uVar7 = uVar7 - 8;
  }
  bVar20 = bVar20 & ~(byte)(-1 << (uint)*(byte *)(param_1 + 0x79));
  *(byte *)(param_1 + 0x6b) = bVar20;
  uVar11 = (uint)*(byte *)(param_1 + 0x7a);
  *(char *)(param_1 + 0x6e) = *(char *)(param_1 + 0x92);
  *(char *)(param_1 + 0x6c) = (char)uVar7;
  *(bool *)(param_1 + 0x6f) = *(char *)(param_1 + 0x92) == '\0';
  uVar15 = uVar7 + uVar11;
  bVar28 = *pbVar14 >> (uVar7 & 0xff);
  pbVar21 = pbVar14;
  if (7 < (uVar15 & 0xff)) {
    pbVar21 = pbVar14 + 1;
    *(byte **)(param_1 + 0x60) = pbVar21;
    bVar28 = bVar28 | pbVar14[1] << (8 - uVar7 & 0xff);
    uVar15 = uVar15 - 8;
  }
  uVar23 = (uint)*(byte *)(param_1 + 0x7b);
  *(char *)(param_1 + 0x6c) = (char)uVar15;
  uVar7 = uVar23 + uVar15;
  bVar16 = *pbVar21 >> (uVar15 & 0xff);
  pbVar14 = pbVar21;
  if (7 < (uVar7 & 0xff)) {
    pbVar14 = pbVar21 + 1;
    *(byte **)(param_1 + 0x60) = pbVar14;
    bVar16 = bVar16 | pbVar21[1] << (8 - uVar15 & 0xff);
    uVar7 = uVar7 - 8;
  }
  iVar25 = (int)(char)bVar1;
  uVar15 = (uint)*(byte *)(param_1 + 0x7c);
  *(char *)(param_1 + 0x6c) = (char)uVar7;
  cVar4 = (char)(uVar15 + uVar7);
  bVar13 = *pbVar14 >> (uVar7 & 0xff);
  if (7 < (uVar15 + uVar7 & 0xff)) {
    *(byte **)(param_1 + 0x60) = pbVar14 + 1;
    bVar13 = bVar13 | pbVar14[1] << (8 - uVar7 & 0xff);
    cVar4 = cVar4 + -8;
  }
  *(char *)(param_1 + 0x6c) = cVar4;
  if (iVar25 < 1) goto LAB_08010736;
  iVar22 = (int)(char)((char)(-1 << (uVar11 - 1 & 0xff)) + (bVar28 & ~(byte)(-1 << uVar11)));
  uVar2 = *(undefined1 *)(param_1 + 0x70);
  iVar24 = (int)(char)((char)(1 << (uVar23 - 1 & 0xff)) -
                      (bVar20 + (bVar16 & ~(byte)(-1 << uVar23))));
  sVar5 = FUN_080100c0(*(undefined2 *)(param_1 + 100),iVar22,iVar24,uVar2);
  *(short *)(param_1 + 100) = sVar5;
  sVar6 = FUN_080100e4(*(undefined2 *)(param_1 + 0x66),iVar22,iVar24,uVar2);
  *(short *)(param_1 + 0x66) = sVar6;
  sVar10 = sVar6;
  sVar12 = sVar5;
  switch(uVar2) {
  case 0:
    sVar10 = (char)bVar20 + sVar6;
    sVar12 = sVar5 + (char)bVar1;
    break;
  case 1:
    sVar12 = sVar5 + 1;
    sVar5 = (sVar5 - (char)bVar20) + 1;
    sVar10 = sVar6 + (char)bVar1;
    break;
  case 2:
    sVar12 = 1;
    sVar17 = (sVar5 - (char)bVar1) + 1;
    iVar25 = (int)(char)bVar20;
    goto LAB_080103de;
  case 3:
    sVar12 = (short)(char)bVar20;
    sVar17 = sVar5;
LAB_080103de:
    sVar12 = sVar12 + sVar5;
    sVar10 = sVar6 + 1;
    sVar6 = (sVar6 - (short)iVar25) + 1;
    sVar5 = sVar17;
  }
  iVar25 = FUN_0800fea4(param_1,sVar5,sVar6,sVar12,sVar10);
  if (iVar25 != 0) {
    uVar11 = (uint)*(byte *)(param_1 + 0x6c);
    pbVar14 = *(byte **)(param_1 + 0x60);
    iVar25 = 0;
    iVar22 = 0;
    *(undefined2 *)(param_1 + 0x68) = 0;
    do {
      uVar23 = uVar11 + *(byte *)(param_1 + 0x76);
      uVar7 = (uint)(*pbVar14 >> (uVar11 & 0xff));
      pbVar21 = pbVar14;
      if (7 < (uVar23 & 0xff)) {
        pbVar21 = pbVar14 + 1;
        *(byte **)(param_1 + 0x60) = pbVar21;
        uVar7 = uVar7 | (uint)pbVar14[1] << (8 - uVar11 & 0xff);
        uVar23 = uVar23 - 8;
      }
      *(char *)(param_1 + 0x6c) = (char)uVar23;
      uVar11 = *(byte *)(param_1 + 0x77) + uVar23;
      cVar4 = (char)uVar11;
      uVar18 = (uint)(*pbVar21 >> (uVar23 & 0xff));
      if (7 < (uVar11 & 0xff)) {
        *(byte **)(param_1 + 0x60) = pbVar21 + 1;
        uVar18 = uVar18 | (uint)pbVar21[1] << (8 - uVar23 & 0xff);
        cVar4 = cVar4 + -8;
      }
      uVar7 = uVar7 & ~(-1 << (uint)*(byte *)(param_1 + 0x76));
      uVar18 = uVar18 & ~(-1 << (uint)*(byte *)(param_1 + 0x77));
      *(char *)(param_1 + 0x6c) = cVar4;
      do {
        uVar23 = (uint)*(byte *)(param_1 + 0x6a);
        uVar19 = uVar23 - iVar22;
        uVar26 = uVar7 & 0xff;
        uVar27 = uVar19 & 0xff;
        uVar11 = uVar7;
        if (*(char *)(param_1 + 0x6d) == '\0') {
          uVar2 = *(undefined1 *)(param_1 + 0x70);
          uVar8 = FUN_080100e4(*(undefined2 *)(param_1 + 0x66),(int)(char)iVar22,(int)(char)iVar25,
                               uVar2);
          uVar9 = FUN_080100c0(*(undefined2 *)(param_1 + 100),(int)(char)iVar22,(int)(char)iVar25,
                               uVar2);
          uVar23 = uVar27;
          if (uVar26 < uVar27) {
            uVar23 = uVar26;
          }
          *(undefined1 *)(param_1 + 0x92) = *(undefined1 *)(param_1 + 0x6f);
          FUN_0800fd88(param_1,uVar9,uVar8,uVar23,uVar2);
          if (uVar27 <= uVar26) {
            uVar23 = uVar7 - uVar19;
            do {
              uVar11 = uVar23;
              uVar19 = (uint)*(byte *)(param_1 + 0x6a);
              iVar25 = (int)(char)((char)iVar25 + '\x01');
              if (*(char *)(param_1 + 0x6d) == '\0') {
                uVar2 = *(undefined1 *)(param_1 + 0x70);
                uVar8 = FUN_080100e4(*(undefined2 *)(param_1 + 0x66),0,iVar25,uVar2);
                uVar9 = FUN_080100c0(*(undefined2 *)(param_1 + 100),0,iVar25,uVar2);
                uVar23 = uVar11 & 0xff;
                if (uVar19 <= (uVar11 & 0xff)) {
                  uVar23 = uVar19;
                }
                *(undefined1 *)(param_1 + 0x92) = *(undefined1 *)(param_1 + 0x6f);
                FUN_0800fd88(param_1,uVar9,uVar8,uVar23,uVar2);
              }
              uVar23 = uVar11 - uVar19;
            } while (uVar19 <= (uVar11 & 0xff));
            goto LAB_08010550;
          }
        }
        else if (uVar27 <= uVar26) {
          iVar25 = iVar25 + 1;
          for (uVar11 = uVar7 - uVar19; uVar23 <= (uVar11 & 0xff); uVar11 = uVar11 - uVar23) {
            uVar11 = uVar11 - uVar23;
            if ((uVar11 & 0xff) < uVar23) {
              iVar25 = iVar25 + 1;
              break;
            }
            uVar11 = uVar11 - uVar23;
            if ((uVar11 & 0xff) < uVar23) {
              iVar25 = iVar25 + 2;
              break;
            }
            uVar11 = uVar11 - uVar23;
            if ((uVar11 & 0xff) < uVar23) {
              iVar25 = iVar25 + 3;
              break;
            }
            iVar25 = iVar25 + 4;
          }
LAB_08010550:
          iVar22 = 0;
        }
        cVar4 = (char)(uVar11 + iVar22);
        iVar24 = (int)cVar4;
        *(char *)(param_1 + 0x68) = cVar4;
        uVar23 = (uint)*(byte *)(param_1 + 0x6a) - (uVar11 + iVar22);
        uVar2 = *(undefined1 *)(param_1 + 0x70);
        uVar19 = uVar23 & 0xff;
        uVar26 = uVar18 & 0xff;
        cVar4 = (char)iVar25;
        *(char *)(param_1 + 0x69) = cVar4;
        uVar3 = *(undefined2 *)(param_1 + 0x66);
        uVar11 = uVar19;
        if (uVar26 < uVar19) {
          uVar11 = uVar26;
        }
        uVar8 = FUN_080100c0(*(undefined2 *)(param_1 + 100),iVar24,(int)cVar4,uVar2);
        uVar9 = FUN_080100e4(uVar3,iVar24,(int)cVar4,uVar2);
        *(undefined1 *)(param_1 + 0x92) = *(undefined1 *)(param_1 + 0x6e);
        FUN_0800fd88(param_1,uVar8,uVar9,uVar11,uVar2);
        uVar11 = uVar18;
        if (uVar19 <= uVar26) {
          uVar23 = uVar18 - uVar23;
          do {
            uVar11 = uVar23;
            uVar19 = (uint)*(byte *)(param_1 + 0x6a);
            uVar2 = *(undefined1 *)(param_1 + 0x70);
            iVar25 = (int)(char)((char)iVar25 + '\x01');
            uVar26 = uVar11 & 0xff;
            uVar3 = *(undefined2 *)(param_1 + 0x66);
            uVar23 = uVar19;
            if (uVar26 < uVar19) {
              uVar23 = uVar26;
            }
            uVar8 = FUN_080100c0(*(undefined2 *)(param_1 + 100),0,iVar25,uVar2);
            uVar9 = FUN_080100e4(uVar3,0,iVar25,uVar2);
            *(undefined1 *)(param_1 + 0x92) = *(undefined1 *)(param_1 + 0x6e);
            FUN_0800fd88(param_1,uVar8,uVar9,uVar23,uVar2);
            uVar23 = uVar11 - uVar19;
          } while (uVar19 <= uVar26);
          iVar24 = 0;
        }
        iVar22 = uVar11 + iVar24;
        pbVar21 = *(byte **)(param_1 + 0x60);
        uVar19 = (uint)*(byte *)(param_1 + 0x6c);
        *(char *)(param_1 + 0x68) = (char)iVar22;
        *(char *)(param_1 + 0x69) = (char)iVar25;
        uVar11 = uVar19 + 1;
        uVar23 = (uint)(*pbVar21 >> uVar19);
        pbVar14 = pbVar21;
        if (7 < (uVar11 & 0xff)) {
          pbVar14 = pbVar21 + 1;
          *(byte **)(param_1 + 0x60) = pbVar14;
          uVar23 = uVar23 | (uint)pbVar21[1] << (8 - uVar19 & 0xff);
          uVar11 = uVar19 - 7;
        }
        *(char *)(param_1 + 0x6c) = (char)uVar11;
      } while ((uVar23 & 1) != 0);
    } while ((char)iVar25 < (char)bVar20);
    *(undefined1 *)(param_1 + 0x92) = *(undefined1 *)(param_1 + 0x6e);
  }
LAB_08010736:
  return (int)(char)((char)(-1 << (uVar15 - 1 & 0xff)) + (bVar13 & ~(byte)(-1 << uVar15)));
}



/* 08010754 */

byte * FUN_08010754(int param_1,uint param_2)

{
  byte bVar1;
  ushort uVar2;
  int iVar3;
  uint uVar4;
  byte *pbVar5;
  ushort *puVar6;
  ushort *puVar7;
  
  pbVar5 = (byte *)(*(int *)(param_1 + 0x58) + 0x17);
  if (0xff < param_2) {
    puVar6 = (ushort *)(pbVar5 + *(ushort *)(param_1 + 0x8a));
    puVar7 = puVar6;
    do {
      iVar3 = FUN_08010820(puVar6,0);
      puVar7 = (ushort *)((int)puVar7 + iVar3);
      uVar4 = FUN_08010820(puVar6,2);
      puVar6 = puVar6 + 2;
    } while (uVar4 < param_2);
    uVar4 = (*puVar7 & 0xff) << 8 | (uint)(*puVar7 >> 8);
    while( true ) {
      if (uVar4 == 0) {
        return (byte *)0x0;
      }
      if (uVar4 == param_2) break;
      uVar2 = *(ushort *)((int)puVar7 + (uint)(byte)puVar7[1]);
      uVar4 = (uVar2 & 0xff) << 8 | (uint)(uVar2 >> 8);
      if (uVar4 == 0) {
        return (byte *)0x0;
      }
      puVar7 = (ushort *)((int)puVar7 + (uint)(byte)puVar7[1]);
      if (uVar4 == param_2) break;
      uVar2 = *(ushort *)((int)puVar7 + (uint)(byte)puVar7[1]);
      uVar4 = (uVar2 & 0xff) << 8 | (uint)(uVar2 >> 8);
      if (uVar4 == 0) {
        return (byte *)0x0;
      }
      puVar7 = (ushort *)((int)puVar7 + (uint)(byte)puVar7[1]);
      if (uVar4 == param_2) break;
      uVar2 = *(ushort *)((int)puVar7 + (uint)(byte)puVar7[1]);
      uVar4 = (uVar2 & 0xff) << 8 | (uint)(uVar2 >> 8);
      if (uVar4 == 0) {
        return (byte *)0x0;
      }
      puVar7 = (ushort *)((int)puVar7 + (uint)(byte)puVar7[1]);
      if (uVar4 == param_2) break;
      uVar2 = *(ushort *)((int)puVar7 + (uint)(byte)puVar7[1]);
      puVar7 = (ushort *)((int)puVar7 + (uint)(byte)puVar7[1]);
      uVar4 = (uVar2 & 0xff) << 8 | (uint)(uVar2 >> 8);
    }
    return (byte *)((int)puVar7 + 3);
  }
  if (param_2 < 0x61) {
    if (param_2 < 0x41) goto LAB_080107de;
    uVar2 = *(ushort *)(param_1 + 0x86);
  }
  else {
    uVar2 = *(ushort *)(param_1 + 0x88);
  }
  pbVar5 = pbVar5 + uVar2;
LAB_080107de:
  bVar1 = pbVar5[1];
  while( true ) {
    if (bVar1 == 0) {
      return (byte *)0x0;
    }
    if (param_2 == *pbVar5) break;
    pbVar5 = pbVar5 + bVar1;
    if (pbVar5[1] == 0) {
      return (byte *)0x0;
    }
    if (param_2 == *pbVar5) break;
    pbVar5 = pbVar5 + pbVar5[1];
    if (pbVar5[1] == 0) {
      return (byte *)0x0;
    }
    if (param_2 == *pbVar5) break;
    pbVar5 = pbVar5 + pbVar5[1];
    if (pbVar5[1] == 0) {
      return (byte *)0x0;
    }
    if (param_2 == *pbVar5) break;
    pbVar5 = pbVar5 + pbVar5[1];
    bVar1 = pbVar5[1];
  }
  return pbVar5 + 2;
}



/* 08010820 */

uint FUN_08010820(int param_1,int param_2)

{
  return ((uint)*(ushort *)(param_1 + param_2) << 0x18 |
         (uint)(*(ushort *)(param_1 + param_2) >> 8) << 0x10) >> 0x10;
}



/* 08010828 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_08010828(void)

{
  _DAT_2001edc8 = FUN_0800c7cc(0,0x2001c084,0x94);
  FUN_0801007c(_DAT_2001edc8,&PTR_FUN_08010b64_1_08013890,&LAB_08010d00_1,&LAB_0801118c_1);
  FUN_08010c50(_DAT_2001edc8);
  FUN_08010c68(_DAT_2001edc8,0);
  FUN_0800fd70(_DAT_2001edc8);
  return;
}



/* 08010878 */

void FUN_08010878(int *param_1,int param_2,uint param_3,ushort param_4,int param_5)

{
  byte bVar1;
  byte bVar2;
  byte *pbVar3;
  byte *pbVar4;
  ushort uVar5;
  ushort uVar6;
  uint uVar7;
  int iVar8;
  int iVar9;
  
  uVar7 = param_3 & 7;
  iVar8 = 1 << uVar7;
  if (1 < *(byte *)((int)param_1 + 0x92)) {
    iVar8 = 0;
  }
  iVar9 = 0;
  if (*(byte *)((int)param_1 + 0x92) != 1) {
    iVar9 = 1 << uVar7;
  }
  pbVar3 = (byte *)(param_2 +
                   param_1[0xd] +
                   ((param_3 & 0xfffffff8) * (uint)*(byte *)(*param_1 + 0x10) & 0xffff));
  bVar1 = (byte)iVar9;
  bVar2 = (byte)iVar8;
  if (param_5 == 0) {
    uVar5 = param_4 & 3;
    pbVar4 = pbVar3;
    uVar6 = param_4;
    if (uVar5 != 0) {
      *pbVar3 = (*pbVar3 | bVar2) ^ bVar1;
      pbVar4 = pbVar3 + 1;
      uVar6 = param_4 - 1;
      if (uVar5 != 1) {
        pbVar3[1] = (pbVar3[1] | bVar2) ^ bVar1;
        if (uVar5 == 2) {
          pbVar4 = pbVar3 + 2;
          uVar6 = param_4 - 2;
        }
        else {
          pbVar3[2] = (pbVar3[2] | bVar2) ^ bVar1;
          pbVar4 = pbVar3 + 3;
          uVar6 = param_4 - 3;
        }
      }
    }
    if (2 < (ushort)(param_4 - 1)) {
      pbVar3 = pbVar4 + -4;
      do {
        pbVar4 = pbVar3 + 4;
        uVar6 = uVar6 - 4;
        *pbVar4 = (*pbVar4 | bVar2) ^ bVar1;
        pbVar3[5] = (pbVar3[5] | bVar2) ^ bVar1;
        pbVar3[6] = (pbVar3[6] | bVar2) ^ bVar1;
        pbVar3[7] = (pbVar3[7] | bVar2) ^ bVar1;
        pbVar3 = pbVar4;
      } while (uVar6 != 0);
    }
  }
  else {
    uVar5 = param_4 & 3;
    uVar6 = param_4;
    if (uVar5 != 0) {
      uVar7 = param_3 + 1 & 7;
      *pbVar3 = (*pbVar3 | bVar2) ^ bVar1;
      if (uVar7 == 0) {
        pbVar3 = pbVar3 + *(ushort *)((int)param_1 + 0x3a);
        if (*(byte *)((int)param_1 + 0x92) < 2) {
          iVar8 = 1;
        }
        if (*(byte *)((int)param_1 + 0x92) != 1) {
          iVar9 = 1;
        }
      }
      else {
        iVar8 = iVar8 << 1;
        iVar9 = iVar9 << 1;
      }
      uVar6 = param_4 - 1;
      if (uVar5 != 1) {
        uVar7 = param_3 + 2 & 7;
        *pbVar3 = (*pbVar3 | (byte)iVar8) ^ (byte)iVar9;
        if (uVar7 == 0) {
          pbVar3 = pbVar3 + *(ushort *)((int)param_1 + 0x3a);
          if (*(byte *)((int)param_1 + 0x92) < 2) {
            iVar8 = 1;
          }
          if (*(byte *)((int)param_1 + 0x92) != 1) {
            iVar9 = 1;
          }
        }
        else {
          iVar8 = iVar8 << 1;
          iVar9 = iVar9 << 1;
        }
        if (uVar5 == 2) {
          uVar6 = param_4 - 2;
        }
        else {
          *pbVar3 = (*pbVar3 | (byte)iVar8) ^ (byte)iVar9;
          uVar7 = param_3 + 3 & 7;
          uVar6 = param_4 - 3;
          if (uVar7 == 0) {
            pbVar3 = pbVar3 + *(ushort *)((int)param_1 + 0x3a);
            if (*(byte *)((int)param_1 + 0x92) < 2) {
              iVar8 = 1;
            }
            if (*(byte *)((int)param_1 + 0x92) != 1) {
              iVar9 = 1;
            }
          }
          else {
            iVar8 = iVar8 << 1;
            iVar9 = iVar9 << 1;
          }
        }
      }
    }
    if ((ushort)(param_4 - 1) < 3) {
      return;
    }
    do {
      while( true ) {
        *pbVar3 = (*pbVar3 | (byte)iVar8) ^ (byte)iVar9;
        if ((uVar7 + 1 & 7) == 0) {
          pbVar3 = pbVar3 + *(ushort *)((int)param_1 + 0x3a);
          if (*(byte *)((int)param_1 + 0x92) < 2) {
            iVar8 = 1;
          }
          if (*(byte *)((int)param_1 + 0x92) != 1) {
            iVar9 = 1;
          }
        }
        else {
          iVar8 = iVar8 << 1;
          iVar9 = iVar9 << 1;
        }
        *pbVar3 = (*pbVar3 | (byte)iVar8) ^ (byte)iVar9;
        if ((uVar7 + 2 & 7) == 0) {
          pbVar3 = pbVar3 + *(ushort *)((int)param_1 + 0x3a);
          if (*(byte *)((int)param_1 + 0x92) < 2) {
            iVar8 = 1;
          }
          if (*(byte *)((int)param_1 + 0x92) != 1) {
            iVar9 = 1;
          }
        }
        else {
          iVar8 = iVar8 << 1;
          iVar9 = iVar9 << 1;
        }
        *pbVar3 = (*pbVar3 | (byte)iVar8) ^ (byte)iVar9;
        if ((uVar7 + 3 & 7) == 0) {
          pbVar3 = pbVar3 + *(ushort *)((int)param_1 + 0x3a);
          if (*(byte *)((int)param_1 + 0x92) < 2) {
            iVar8 = 1;
          }
          if (*(byte *)((int)param_1 + 0x92) != 1) {
            iVar9 = 1;
          }
        }
        else {
          iVar8 = iVar8 << 1;
          iVar9 = iVar9 << 1;
        }
        *pbVar3 = (*pbVar3 | (byte)iVar8) ^ (byte)iVar9;
        if (uVar7 == 4) break;
        iVar8 = iVar8 << 1;
        iVar9 = iVar9 << 1;
        uVar6 = uVar6 - 4;
        uVar7 = uVar7 ^ 4;
        if (uVar6 == 0) {
          return;
        }
      }
      pbVar3 = pbVar3 + *(ushort *)((int)param_1 + 0x3a);
      if (*(byte *)((int)param_1 + 0x92) < 2) {
        iVar8 = 1;
      }
      if (*(byte *)((int)param_1 + 0x92) != 1) {
        iVar9 = 1;
      }
      uVar6 = uVar6 - 4;
      uVar7 = 0;
    } while (uVar6 != 0);
  }
  return;
}



/* 08010afc */

undefined4 FUN_08010afc(undefined1 *param_1)

{
  *param_1 = 8;
  return 0x2001edcc;
}



/* 08010b0c */

void FUN_08010b0c(int *param_1)

{
  byte bVar1;
  byte bVar2;
  int iVar3;
  byte bVar4;
  uint uVar5;
  
  bVar1 = *(byte *)(param_1 + 0xe);
  bVar4 = *(byte *)((int)param_1 + 0x39);
  bVar2 = *(byte *)(*param_1 + 0x11);
  iVar3 = 0;
  uVar5 = 1;
  do {
    FUN_08010c28(param_1,0,bVar4,(uint)*(byte *)(*param_1 + 0x10),
                 param_1[0xd] + (iVar3 * (uint)*(byte *)(*param_1 + 0x10) & 0xfff8));
    if (bVar1 <= uVar5) {
      return;
    }
    bVar4 = bVar4 + 1;
    iVar3 = iVar3 + 8;
    uVar5 = uVar5 + 1;
  } while (bVar4 < bVar2);
  return;
}



/* 08010b64 */

void FUN_08010b64(int *param_1)

{
  byte bVar1;
  byte bVar2;
  byte bVar3;
  ushort uVar4;
  int iVar5;
  
  bVar1 = *(byte *)(param_1 + 0xe);
  uVar4 = (ushort)bVar1;
  iVar5 = *param_1;
  *(ushort *)(param_1 + 0xf) = (ushort)bVar1 << 3;
  bVar2 = *(byte *)((int)param_1 + 0x39);
  bVar3 = *(byte *)(iVar5 + 0x11);
  *(ushort *)((int)param_1 + 0x3a) = (ushort)*(byte *)(iVar5 + 0x10) << 3;
  *(ushort *)((int)param_1 + 0x3e) = (ushort)bVar2 << 3;
  if ((ushort)bVar3 < (ushort)((ushort)bVar2 + (ushort)bVar1)) {
    uVar4 = (ushort)bVar3 - (ushort)bVar2;
  }
  *(ushort *)(param_1 + 0x10) = (ushort)bVar2 << 3;
  *(ushort *)((int)param_1 + 0x42) = (uVar4 + bVar2) * 8;
  param_1[0x11] = *(int *)(iVar5 + 0x14);
  return;
}



/* 08010ba4 */

void FUN_08010ba4(int param_1)

{
  int iVar1;
  
  *(undefined4 *)(param_1 + 0x4c) = *(undefined4 *)(param_1 + 0x40);
  *(undefined2 *)(param_1 + 0x4a) = *(undefined2 *)(param_1 + 0x44);
  *(undefined2 *)(param_1 + 0x48) = 0;
  iVar1 = FUN_0800fea4(param_1,*(undefined2 *)(param_1 + 0x50),*(undefined2 *)(param_1 + 0x54),
                       *(undefined2 *)(param_1 + 0x52),*(undefined2 *)(param_1 + 0x56));
  if (iVar1 != 0) {
    *(undefined1 *)(param_1 + 0x8c) = 1;
    if (*(ushort *)(param_1 + 0x48) < *(ushort *)(param_1 + 0x50)) {
      *(ushort *)(param_1 + 0x48) = *(ushort *)(param_1 + 0x50);
    }
    if (*(ushort *)(param_1 + 0x52) < *(ushort *)(param_1 + 0x4a)) {
      *(ushort *)(param_1 + 0x4a) = *(ushort *)(param_1 + 0x52);
    }
    if (*(ushort *)(param_1 + 0x4c) < *(ushort *)(param_1 + 0x54)) {
      *(ushort *)(param_1 + 0x4c) = *(ushort *)(param_1 + 0x54);
    }
    if (*(ushort *)(param_1 + 0x56) < *(ushort *)(param_1 + 0x4e)) {
      *(ushort *)(param_1 + 0x4e) = *(ushort *)(param_1 + 0x56);
    }
    return;
  }
  *(undefined1 *)(param_1 + 0x8c) = 0;
  return;
}



/* 08010c28 */

void FUN_08010c28(int param_1,undefined1 param_2,undefined1 param_3,undefined1 param_4,
                 undefined4 param_5)

{
  undefined4 local_10;
  undefined1 local_c;
  undefined1 local_b;
  undefined1 local_a;
  
  local_10 = param_5;
  local_c = param_4;
  local_b = param_2;
  local_a = param_3;
  (**(code **)(param_1 + 8))(param_1,0xf,1,&local_10);
  return;
}



/* 08010c50 */

void FUN_08010c50(int param_1)

{
                    /* WARNING: Could not recover jumptable at 0x08010c5a. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (**(code **)(param_1 + 8))(param_1,10,0,0);
  return;
}



/* 08010c68 */

void FUN_08010c68(int param_1,undefined4 param_2)

{
                    /* WARNING: Could not recover jumptable at 0x08010c72. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (**(code **)(param_1 + 8))(param_1,0xb,param_2,0);
  return;
}



/* 08010c74 */

void FUN_08010c74(undefined4 *param_1,undefined4 param_2,undefined4 param_3,undefined4 param_4,
                 undefined4 param_5)

{
  *(undefined2 *)((int)param_1 + 0x23) = 0xff00;
  *(undefined1 *)(param_1 + 10) = 0xff;
  *param_1 = 0;
  *(undefined1 *)((int)param_1 + 0x26) = 0;
  param_1[2] = param_2;
  param_1[3] = param_3;
  param_1[4] = param_4;
  param_1[5] = param_5;
  param_1[6] = 0;
                    /* WARNING: Could not recover jumptable at 0x08010cae. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*(code *)param_1[2])(param_1,9,0,0);
  return;
}



/* 08010cc4 */

void FUN_08010cc4(int param_1)

{
                    /* WARNING: Could not recover jumptable at 0x08010cce. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (**(code **)(param_1 + 0x10))(param_1,0x19,0,0);
  return;
}



/* 08010cd0 */

void FUN_08010cd0(undefined4 param_1,undefined1 param_2)

{
  undefined1 local_9;
  
  local_9 = param_2;
  FUN_08010ce8(param_1,1,&local_9);
  return;
}



/* 08010ce8 */

void FUN_08010ce8(int param_1,undefined4 param_2,undefined4 param_3)

{
                    /* WARNING: Could not recover jumptable at 0x08010cf2. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (**(code **)(param_1 + 0x10))(param_1,0x17,param_2,param_3);
  return;
}



/* 08010cf4 */

void FUN_08010cf4(int param_1)

{
                    /* WARNING: Could not recover jumptable at 0x08010cfe. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (**(code **)(param_1 + 0x10))(param_1,0x18,0,0);
  return;
}



/* 08010dfc */

void FUN_08010dfc(int param_1)

{
                    /* WARNING: Could not recover jumptable at 0x08010e06. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (**(code **)(param_1 + 0xc))(param_1,0x19,0,0);
  return;
}



/* 08010e08 */

void FUN_08010e08(int param_1,undefined4 param_2)

{
                    /* WARNING: Could not recover jumptable at 0x08010e12. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (**(code **)(param_1 + 0xc))(param_1,0x16,param_2,0);
  return;
}



/* 08010e14 */

void FUN_08010e14(int param_1,undefined4 param_2)

{
                    /* WARNING: Could not recover jumptable at 0x08010e1e. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (**(code **)(param_1 + 0xc))(param_1,0x15,param_2,0);
  return;
}



/* 08010e20 */

void FUN_08010e20(int param_1,undefined4 param_2,undefined4 param_3)

{
                    /* WARNING: Could not recover jumptable at 0x08010e2a. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (**(code **)(param_1 + 0xc))(param_1,0x17,param_2,param_3);
  return;
}



/* 08010e2c */

void FUN_08010e2c(int param_1,byte *param_2)

{
  uint uVar1;
  byte local_15;
  
  while( true ) {
    while( true ) {
      while( true ) {
        uVar1 = (uint)*param_2;
        if (0x17 < uVar1) break;
        if (uVar1 - 0x15 < 2) {
          local_15 = param_2[1];
          (**(code **)(param_1 + 0xc))(param_1,uVar1,local_15,0);
          param_2 = param_2 + 2;
        }
        else {
          if (uVar1 != 0x17) {
            return;
          }
          local_15 = param_2[1];
          FUN_08010e20(param_1,1,&local_15);
          param_2 = param_2 + 2;
        }
      }
      if (1 < uVar1 - 0x18) break;
      (**(code **)(param_1 + 0xc))(param_1,uVar1,0,0);
      param_2 = param_2 + 1;
    }
    if (uVar1 != 0xfe) break;
    local_15 = param_2[1];
    FUN_08011204(param_1,0x29);
    param_2 = param_2 + 2;
  }
  return;
}



/* 08010ea8 */

void FUN_08010ea8(int param_1)

{
                    /* WARNING: Could not recover jumptable at 0x08010eb2. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (**(code **)(param_1 + 0xc))(param_1,0x18,0,0);
  return;
}



/* 08011014 */

void FUN_08011014(int *param_1)

{
  (*(code *)param_1[5])(param_1,0x28,0,0);
  (*(code *)param_1[3])(param_1,0x14,0,0);
  FUN_08011204(param_1,0x4b,1);
  FUN_08011204(param_1,0x29,*(undefined1 *)(*param_1 + 4));
  FUN_08011204(param_1,0x4b,0);
  FUN_08011204(param_1,0x29,*(undefined1 *)(*param_1 + 4));
  FUN_08011204(param_1,0x4b,1);
  FUN_08011204(param_1,0x29,*(undefined1 *)(*param_1 + 5));
  return;
}



/* 08011078 */

void FUN_08011078(int *param_1,int param_2)

{
  undefined1 uVar1;
  
  uVar1 = *(undefined1 *)(param_2 + 0x12);
  *param_1 = param_2;
  *(undefined1 *)((int)param_1 + 0x22) = uVar1;
  return;
}



/* 08011084 */

undefined4 FUN_08011084(int *param_1,undefined4 param_2,uint param_3,undefined4 *param_4)

{
  undefined4 uVar1;
  undefined *puVar2;
  byte bVar3;
  
  uVar1 = 0;
  switch(param_2) {
  case 10:
    FUN_08011014(param_1);
    puVar2 = &DAT_08013fb7;
    break;
  case 0xb:
    if (param_3 == 0) {
      puVar2 = &DAT_08013fec;
    }
    else {
      puVar2 = &DAT_08013ff1;
    }
    break;
  default:
    goto switchD_08011096_caseD_c;
  case 0xd:
    if (param_3 == 0) {
      FUN_08010e2c(param_1,&DAT_08013fa9);
      *(undefined1 *)((int)param_1 + 0x22) = *(undefined1 *)(*param_1 + 0x12);
    }
    else {
      FUN_08010e2c(param_1,&DAT_08013fb0);
      *(undefined1 *)((int)param_1 + 0x22) = *(undefined1 *)(*param_1 + 0x13);
    }
    goto LAB_08011152;
  case 0xe:
    FUN_08010ea8(param_1);
    FUN_08010e14(param_1,0x81);
    FUN_08010e08(param_1,param_3);
    goto LAB_0801114c;
  case 0xf:
    FUN_08010ea8(param_1);
    bVar3 = *(char *)((int)param_1 + 0x22) + *(char *)((int)param_4 + 5) * '\b';
    FUN_08010e14(param_1,(bVar3 >> 4) + 0x10);
    FUN_08010e14(param_1,bVar3 & 0xf);
    FUN_08010e14(param_1,*(byte *)((int)param_4 + 6) | 0xb0);
    do {
      FUN_08010e20(param_1,*(char *)(param_4 + 1) << 3,*param_4);
      param_3 = param_3 - 1;
    } while ((param_3 & 0xff) != 0);
LAB_0801114c:
    FUN_08010dfc(param_1);
    goto LAB_08011152;
  }
  FUN_08010e2c(param_1,puVar2);
LAB_08011152:
  uVar1 = 1;
switchD_08011096_caseD_c:
  return uVar1;
}



/* 08011204 */

void FUN_08011204(int param_1)

{
                    /* WARNING: Could not recover jumptable at 0x0801120a. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (**(code **)(param_1 + 0x14))();
  return;
}



/* 0801120c */

void FUN_0801120c(int param_1,undefined4 param_2,undefined4 param_3)

{
  FUN_08010cf4();
  FUN_08010cd0(param_1,0x40);
  (**(code **)(param_1 + 0x10))(param_1,0x17,param_2,param_3);
  FUN_08010cc4(param_1);
  return;
}



/* 0801123c */

void FUN_0801123c(int param_1)

{
  *(undefined1 *)(param_1 + 0x26) = 0;
  return;
}



/* 08011244 */

int FUN_08011244(int param_1)

{
  int *piVar1;
  int iVar2;
  int iVar3;
  int iVar4;
  
  piVar1 = *(int **)(param_1 + 0x10);
  iVar3 = *(int *)(param_1 + 4);
  iVar2 = *(int *)(param_1 + 8);
  iVar4 = piVar1[1];
  *(int *)(iVar3 + 8) = iVar2;
  *(int *)(iVar2 + 4) = iVar3;
  if (iVar4 == param_1) {
    piVar1[1] = iVar2;
  }
  *(undefined4 *)(param_1 + 0x10) = 0;
  *piVar1 = *piVar1 + -1;
  return *piVar1;
}



/* 08011268 */

void FUN_08011268(undefined4 *param_1,undefined4 *param_2,undefined4 *param_3)

{
  *param_1 = 0x2001f3d0;
  *param_2 = 0x2001f1d0;
  *param_3 = 0x80;
  return;
}



/* 08011284 */

void FUN_08011284(undefined4 *param_1,undefined4 *param_2,undefined4 *param_3)

{
  *param_1 = 0x2001f42c;
  *param_2 = 0x20016000;
  *param_3 = 0x1800;
  return;
}



/* 080112a0 */

void FUN_080112a0(void)

{
  return;
}



/* 080112a4 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_080112a4(void)

{
  DAT_2001c394 = 0;
  _DAT_2001c398 = _DAT_2001c398 + 1;
  return;
}



/* 080112ac */

void FUN_080112ac(undefined4 *param_1)

{
  undefined4 *puVar1;
  
  puVar1 = param_1 + 2;
  *puVar1 = 0xffffffff;
  param_1[1] = puVar1;
  param_1[3] = puVar1;
  param_1[4] = puVar1;
  *param_1 = 0;
  return;
}



/* 080112c4 */

void FUN_080112c4(int param_1)

{
  *(undefined4 *)(param_1 + 0x10) = 0;
  return;
}



/* 080112cc */

void FUN_080112cc(int *param_1,uint *param_2)

{
  uint *puVar1;
  uint *puVar2;
  uint *puVar3;
  uint uVar4;
  
  uVar4 = *param_2;
  if (uVar4 == 0xffffffff) {
    puVar2 = (uint *)param_1[4];
    puVar3 = (uint *)((uint *)param_1[4])[1];
  }
  else {
    puVar3 = (uint *)(param_1 + 2);
    do {
      puVar1 = (uint *)puVar3[1];
      puVar2 = puVar3;
      puVar3 = puVar1;
      if (((uVar4 < *puVar1) || (puVar3 = (uint *)puVar1[1], puVar2 = puVar1, uVar4 < *puVar3)) ||
         (puVar1 = (uint *)puVar3[1], puVar2 = puVar3, puVar3 = puVar1, uVar4 < *puVar1)) break;
      puVar3 = (uint *)puVar1[1];
      puVar2 = puVar1;
    } while (*puVar3 <= uVar4);
  }
  param_2[1] = (uint)puVar3;
  puVar3[2] = (uint)param_2;
  param_2[2] = (uint)puVar2;
  puVar2[1] = (uint)param_2;
  param_2[4] = (uint)param_1;
  *param_1 = *param_1 + 1;
  return;
}



/* 08011330 */

void FUN_08011330(int *param_1,int param_2)

{
  int iVar1;
  int iVar2;
  int iVar3;
  
  iVar3 = *param_1;
  iVar2 = param_1[1];
  *(int **)(param_2 + 0x10) = param_1;
  iVar1 = *(int *)(iVar2 + 8);
  *(int *)(param_2 + 4) = iVar2;
  *(int *)(param_2 + 8) = iVar1;
  *(int *)(iVar1 + 4) = param_2;
  *(int *)(iVar2 + 8) = param_2;
  *param_1 = iVar3 + 1;
  return;
}



/* 0801134c */

void FUN_0801134c(void)

{
  *DAT_0801135c = *DAT_0801135c | 0xf00000;
  return;
}



/* 08011360 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_08011360(void)

{
  bool bVar1;
  int iVar2;
  
  iVar2 = _DAT_2001c09c;
  bVar1 = (bool)isCurrentModePrivileged();
  if (bVar1) {
    setBasePriority(0x50);
  }
  InstructionSynchronizationBarrier(0xf);
  DataSynchronizationBarrier(0xf);
  _DAT_2001c09c = _DAT_2001c09c + 1;
  if (iVar2 != 0) {
    return;
  }
  if ((_DAT_e000ed04 & 0xff) == 0) {
    return;
  }
  bVar1 = (bool)isCurrentModePrivileged();
  if (bVar1) {
    setBasePriority(0x50);
  }
  InstructionSynchronizationBarrier(0xf);
  DataSynchronizationBarrier(0xf);
  do {
                    /* WARNING: Do nothing block with infinite loop */
  } while( true );
}



/* 080113a8 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined1 * FUN_080113a8(void)

{
  bool bVar1;
  
  if (_DAT_2001c09c == 0) {
    bVar1 = (bool)isCurrentModePrivileged();
    if (bVar1) {
      setBasePriority(0x50);
    }
    InstructionSynchronizationBarrier(0xf);
    DataSynchronizationBarrier(0xf);
    do {
                    /* WARNING: Do nothing block with infinite loop */
    } while( true );
  }
  _DAT_2001c09c = _DAT_2001c09c + -1;
  if (_DAT_2001c09c != 0) {
    return &DAT_2001c09c;
  }
  bVar1 = (bool)isCurrentModePrivileged();
  if (bVar1) {
    setBasePriority(0);
  }
  return (undefined1 *)0x0;
}



/* 080113d8 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_080113d8(int param_1)

{
  bool bVar1;
  int iVar2;
  uint uVar3;
  int *piVar4;
  int *piVar5;
  int *piVar6;
  int *piVar7;
  int iVar8;
  int *piVar9;
  
  if (param_1 == 0) {
    return;
  }
  uVar3 = 0;
  if (DAT_2001c31c != '\0') {
    uVar3 = 0x80000000;
  }
  if ((uVar3 & *(uint *)(param_1 + -4)) == 0) {
    bVar1 = (bool)isCurrentModePrivileged();
    if (bVar1) {
      setBasePriority(0x50);
    }
    InstructionSynchronizationBarrier(0xf);
    DataSynchronizationBarrier(0xf);
    do {
                    /* WARNING: Do nothing block with infinite loop */
    } while( true );
  }
  piVar9 = (int *)(param_1 + -8);
  if (*piVar9 != 0) {
    bVar1 = (bool)isCurrentModePrivileged();
    if (bVar1) {
      setBasePriority(0x50);
    }
    InstructionSynchronizationBarrier(0xf);
    DataSynchronizationBarrier(0xf);
    do {
                    /* WARNING: Do nothing block with infinite loop */
    } while( true );
  }
  *(uint *)(param_1 + -4) = *(uint *)(param_1 + -4) & ~uVar3;
  FUN_080119a0();
  iVar2 = *(int *)(param_1 + -4);
  _DAT_2001c324 = _DAT_2001c324 + iVar2;
  piVar4 = (int *)&DAT_2001c334;
  while (piVar6 = (int *)*piVar4, piVar5 = piVar4, piVar6 < piVar9) {
    piVar4 = (int *)*piVar6;
    if (piVar9 <= piVar4) {
      iVar8 = piVar6[1];
      piVar7 = (int *)((int)piVar6 + iVar8);
      piVar5 = piVar6;
      piVar6 = piVar4;
      goto joined_r0x08011484;
    }
    piVar7 = (int *)*piVar4;
    piVar6 = piVar7;
    piVar5 = piVar4;
    if ((piVar9 <= piVar7) ||
       (piVar4 = (int *)*piVar7, piVar6 = piVar4, piVar5 = piVar7, piVar9 <= piVar4)) break;
  }
  iVar8 = piVar5[1];
  piVar7 = (int *)((int)piVar5 + iVar8);
joined_r0x08011484:
  if (piVar7 == piVar9) {
    iVar2 = iVar2 + iVar8;
    piVar5[1] = iVar2;
    piVar4 = (int *)((int)piVar5 + iVar2);
    piVar9 = piVar5;
  }
  else {
    piVar4 = (int *)((int)piVar9 + iVar2);
  }
  piVar7 = piVar6;
  if ((piVar4 == piVar6) && (piVar7 = _DAT_2001c320, piVar6 != _DAT_2001c320)) {
    piVar7 = (int *)*piVar6;
    piVar9[1] = iVar2 + piVar6[1];
  }
  *piVar9 = (int)piVar7;
  if (piVar5 != piVar9) {
    *piVar5 = (int)piVar9;
  }
  _DAT_2001c330 = _DAT_2001c330 + 1;
  FUN_08012fd0();
  return;
}



/* 080114b8 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_080114b8(void)

{
  _DAT_e000e018 = 0;
  _DAT_e000e014 = _DAT_2001c064 / 1000 - 1;
  _DAT_e000e010 = 7;
  return;
}



/* 080114ec */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_080114ec(void)

{
  bool bVar1;
  uint uVar2;
  
  uVar2 = 0;
  bVar1 = (bool)isCurrentModePrivileged();
  if (bVar1) {
    uVar2 = getCurrentExceptionNumber();
    uVar2 = uVar2 & 0x1ff;
  }
  if ((0xf < uVar2) && (*(byte *)(uVar2 + 0xe000e3f0) < DAT_2001c33c)) {
    bVar1 = (bool)isCurrentModePrivileged();
    if (bVar1) {
      setBasePriority(0x50);
    }
    InstructionSynchronizationBarrier(0xf);
    DataSynchronizationBarrier(0xf);
    do {
                    /* WARNING: Do nothing block with infinite loop */
    } while( true );
  }
  if ((_DAT_e000ed0c & 0x700) <= _DAT_2001c340) {
    return;
  }
  bVar1 = (bool)isCurrentModePrivileged();
  if (bVar1) {
    setBasePriority(0x50);
  }
  InstructionSynchronizationBarrier(0xf);
  DataSynchronizationBarrier(0xf);
  do {
                    /* WARNING: Do nothing block with infinite loop */
  } while( true );
}



/* 0801154c */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_0801154c(int param_1,int param_2)

{
  int *piVar1;
  
  if (_DAT_2001f488 == 0) {
    piVar1 = (int *)&DAT_2001f488;
  }
  else {
    piVar1 = (int *)&DAT_2001f490;
    if ((((_DAT_2001f490 != 0) && (piVar1 = (int *)&DAT_2001f498, _DAT_2001f498 != 0)) &&
        (piVar1 = (int *)&DAT_2001f4a0, _DAT_2001f4a0 != 0)) &&
       (((piVar1 = (int *)&DAT_2001f4a8, _DAT_2001f4a8 != 0 &&
         (piVar1 = (int *)&DAT_2001f4b0, _DAT_2001f4b0 != 0)) &&
        (piVar1 = (int *)&DAT_2001f4b8, _DAT_2001f4b8 != 0)))) {
      if (_DAT_2001f4c0 == 0) {
        _DAT_2001f4c0 = param_2;
        _DAT_2001f4c4 = param_1;
      }
      return;
    }
  }
  *piVar1 = param_2;
  piVar1[1] = param_1;
  return;
}



/* 080115a4 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_080115a4(int param_1)

{
  bool bVar1;
  undefined4 *puVar2;
  
  if (param_1 == 0) {
    bVar1 = (bool)isCurrentModePrivileged();
    if (bVar1) {
      setBasePriority(0x50);
    }
    InstructionSynchronizationBarrier(0xf);
    DataSynchronizationBarrier(0xf);
    do {
                    /* WARNING: Do nothing block with infinite loop */
    } while( true );
  }
  puVar2 = (undefined4 *)&DAT_2001f488;
  if (_DAT_2001f48c != param_1) {
    if (_DAT_2001f494 == param_1) {
      puVar2 = (undefined4 *)&DAT_2001f490;
    }
    else if (_DAT_2001f49c == param_1) {
      puVar2 = (undefined4 *)&DAT_2001f498;
    }
    else if (_DAT_2001f4a4 == param_1) {
      puVar2 = (undefined4 *)&DAT_2001f4a0;
    }
    else if (_DAT_2001f4ac == param_1) {
      puVar2 = (undefined4 *)&DAT_2001f4a8;
    }
    else if (_DAT_2001f4b4 == param_1) {
      puVar2 = (undefined4 *)&DAT_2001f4b0;
    }
    else if (_DAT_2001f4bc == param_1) {
      puVar2 = (undefined4 *)&DAT_2001f4b8;
    }
    else {
      if (_DAT_2001f4c4 != param_1) goto LAB_08011614;
      puVar2 = (undefined4 *)&DAT_2001f4c0;
    }
  }
  *puVar2 = 0;
  puVar2[1] = 0;
LAB_08011614:
  if (*(char *)(param_1 + 0x46) != '\0') {
    return;
  }
  FUN_080113d8();
  return;
}



/* 08011624 */

void FUN_08011624(int param_1,undefined4 param_2,undefined4 param_3)

{
  FUN_08011360();
  if (*(char *)(param_1 + 0x44) == -1) {
    *(undefined1 *)(param_1 + 0x44) = 0;
  }
  if (*(char *)(param_1 + 0x45) == -1) {
    *(undefined1 *)(param_1 + 0x45) = 0;
  }
  FUN_080113a8();
  if (*(int *)(param_1 + 0x38) == 0) {
    FUN_08011790(param_1 + 0x24,param_2,param_3);
    FUN_0800eca8(param_1);
    return;
  }
  FUN_0800eca8(param_1);
  return;
}



/* 08011678 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_08011678(uint param_1)

{
  bool bVar1;
  uint uVar2;
  int iVar3;
  uint uVar4;
  
  uVar2 = _DAT_2001c280;
  if (param_1 != 0) {
    if (_DAT_2001c27c != 0) {
      bVar1 = (bool)isCurrentModePrivileged();
      if (bVar1) {
        setBasePriority(0x50);
      }
      InstructionSynchronizationBarrier(0xf);
      DataSynchronizationBarrier(0xf);
      do {
                    /* WARNING: Do nothing block with infinite loop */
      } while( true );
    }
    _DAT_2001c27c = 1;
    FUN_08011244(_DAT_2001c268 + 4);
    uVar4 = uVar2 + param_1;
    *(uint *)(_DAT_2001c268 + 4) = uVar4;
    if (CARRY4(uVar2,param_1)) {
      FUN_080112cc(_DAT_2001c288,_DAT_2001c268 + 4);
    }
    else {
      FUN_080112cc(_DAT_2001c284,_DAT_2001c268 + 4);
      if (uVar4 < _DAT_2001c294) {
        _DAT_2001c294 = uVar4;
      }
    }
    iVar3 = FUN_08012fd0();
    if (iVar3 != 0) {
      return;
    }
  }
  _DAT_e000ed04 = 0x10000000;
  DataSynchronizationBarrier(0xf);
  InstructionSynchronizationBarrier(0xf);
  return;
}



/* 080116f8 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_080116f8(undefined4 *param_1)

{
  *param_1 = _DAT_2001c2a0;
  param_1[1] = _DAT_2001c280;
  return;
}



/* 0801170c */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_0801170c(void)

{
  _DAT_2001c298 = 1;
  return;
}



/* 0801171c */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_0801171c(int param_1,uint param_2)

{
  bool bVar1;
  uint uVar2;
  uint uVar3;
  
  if (param_1 == 0) {
    bVar1 = (bool)isCurrentModePrivileged();
    if (bVar1) {
      setBasePriority(0x50);
    }
    InstructionSynchronizationBarrier(0xf);
    DataSynchronizationBarrier(0xf);
    do {
                    /* WARNING: Do nothing block with infinite loop */
    } while( true );
  }
  FUN_080112cc(param_1,_DAT_2001c268 + 0x18);
  uVar2 = _DAT_2001c280;
  FUN_08011244(_DAT_2001c268 + 4);
  if (param_2 != 0xffffffff) {
    uVar3 = param_2 + uVar2;
    *(uint *)(_DAT_2001c268 + 4) = uVar3;
    if (CARRY4(param_2,uVar2)) {
      FUN_080112cc(_DAT_2001c288,_DAT_2001c268 + 4);
      return;
    }
    FUN_080112cc(_DAT_2001c284,_DAT_2001c268 + 4);
    if (uVar3 < _DAT_2001c294) {
      _DAT_2001c294 = uVar3;
    }
    return;
  }
  FUN_08011330(0x2001c2b8,_DAT_2001c268 + 4);
  return;
}



/* 08011790 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_08011790(int param_1,uint param_2,int param_3)

{
  bool bVar1;
  uint uVar2;
  uint uVar3;
  
  if (param_1 == 0) {
    bVar1 = (bool)isCurrentModePrivileged();
    if (bVar1) {
      setBasePriority(0x50);
    }
    InstructionSynchronizationBarrier(0xf);
    DataSynchronizationBarrier(0xf);
    do {
                    /* WARNING: Do nothing block with infinite loop */
    } while( true );
  }
  FUN_08011330(param_1,_DAT_2001c268 + 0x18);
  uVar2 = _DAT_2001c280;
  FUN_08011244(_DAT_2001c268 + 4);
  if (param_3 != 0) {
    FUN_08011330(0x2001c2b8,_DAT_2001c268 + 4);
    return;
  }
  uVar3 = param_2 + uVar2;
  *(uint *)(_DAT_2001c268 + 4) = uVar3;
  if (CARRY4(param_2,uVar2)) {
    FUN_080112cc(_DAT_2001c288,_DAT_2001c268 + 4);
    return;
  }
  FUN_080112cc(_DAT_2001c284,_DAT_2001c268 + 4);
  if (uVar3 < _DAT_2001c294) {
    _DAT_2001c294 = uVar3;
  }
  return;
}



/* 0801180c */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_0801180c(int param_1,uint param_2)

{
  bool bVar1;
  uint uVar2;
  
  if (param_1 != 0) {
    if (*(int *)(param_1 + 0x50) == 0) {
      bVar1 = (bool)isCurrentModePrivileged();
      if (bVar1) {
        setBasePriority(0x50);
      }
      InstructionSynchronizationBarrier(0xf);
      DataSynchronizationBarrier(0xf);
      do {
                    /* WARNING: Do nothing block with infinite loop */
      } while( true );
    }
    if (param_2 < *(uint *)(param_1 + 0x4c)) {
      param_2 = *(uint *)(param_1 + 0x4c);
    }
    if ((*(int *)(param_1 + 0x50) == 1) && (uVar2 = *(uint *)(param_1 + 0x2c), uVar2 != param_2)) {
      if (param_1 == _DAT_2001c268) {
        bVar1 = (bool)isCurrentModePrivileged();
        if (bVar1) {
          setBasePriority(0x50);
        }
        InstructionSynchronizationBarrier(0xf);
        DataSynchronizationBarrier(0xf);
        do {
                    /* WARNING: Do nothing block with infinite loop */
        } while( true );
      }
      *(uint *)(param_1 + 0x2c) = param_2;
      if (-1 < *(int *)(param_1 + 0x18)) {
        *(uint *)(param_1 + 0x18) = 0x38 - param_2;
      }
      if (*(undefined1 **)(param_1 + 0x14) == &DAT_2001e910 + uVar2 * 0x14) {
        FUN_08011244(param_1 + 4);
        uVar2 = *(uint *)(param_1 + 0x2c);
        if (_DAT_2001c28c < uVar2) {
          _DAT_2001c28c = uVar2;
        }
        FUN_08011330(&DAT_2001e910 + uVar2 * 0x14,param_1 + 4);
        return;
      }
    }
  }
  return;
}



/* 080118b0 */

/* WARNING: Removing unreachable block (ram,0x08011970) */
/* WARNING: Removing unreachable block (ram,0x08011974) */
/* WARNING: Removing unreachable block (ram,0x08011978) */
/* WARNING: Removing unreachable block (ram,0x08011980) */
/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_080118b0(void)

{
  bool bVar1;
  int iVar2;
  undefined4 local_18;
  int local_14;
  int local_10;
  int local_c;
  
  local_14 = 0;
  local_10 = 0;
  FUN_08011268(&local_10,&local_14,&local_18);
  iVar2 = local_10;
  if (local_14 == 0) {
    bVar1 = (bool)isCurrentModePrivileged();
    if (bVar1) {
      setBasePriority(0x50);
    }
    InstructionSynchronizationBarrier(0xf);
    DataSynchronizationBarrier(0xf);
    do {
                    /* WARNING: Do nothing block with infinite loop */
    } while( true );
  }
  if (local_10 == 0) {
    bVar1 = (bool)isCurrentModePrivileged();
    if (bVar1) {
      setBasePriority(0x50);
    }
    InstructionSynchronizationBarrier(0xf);
    DataSynchronizationBarrier(0xf);
    do {
                    /* WARNING: Do nothing block with infinite loop */
    } while( true );
  }
  local_c = 0x5c;
  *(int *)(local_10 + 0x30) = local_14;
  *(undefined1 *)(local_10 + 0x59) = 2;
  FUN_0800e710(&LAB_0800e684_1,&DAT_08011998,local_18,0,0,&local_c,local_10);
  FUN_0800e3f8(iVar2);
  _DAT_2001c290 = local_c;
  if (local_c != 0) {
    iVar2 = FUN_08013150();
    if (iVar2 == -1) {
      bVar1 = (bool)isCurrentModePrivileged();
      if (bVar1) {
        setBasePriority(0x50);
      }
      InstructionSynchronizationBarrier(0xf);
      DataSynchronizationBarrier(0xf);
      do {
                    /* WARNING: Do nothing block with infinite loop */
      } while( true );
    }
    if (iVar2 == 1) {
      bVar1 = (bool)isCurrentModePrivileged();
      if (bVar1) {
        setBasePriority(0x50);
      }
      InstructionSynchronizationBarrier(0xf);
      DataSynchronizationBarrier(0xf);
      _DAT_2001c294 = 0xffffffff;
      _DAT_2001c278 = 1;
      _DAT_2001c280 = 0;
      FUN_08011af0();
    }
  }
  return;
}



/* 080119a0 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_080119a0(void)

{
  _DAT_2001c27c = _DAT_2001c27c + 1;
  return;
}



/* 080119b0 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_080119b0(void)

{
  bool bVar1;
  int *piVar2;
  int iVar3;
  int *piVar4;
  
  if (_DAT_2001c27c != 0) {
    _DAT_2001c298 = 1;
    return;
  }
  _DAT_2001c298 = 0;
  piVar4 = (int *)(&DAT_2001e910 + _DAT_2001c28c * 0x14);
  if (*(int *)(&DAT_2001e910 + _DAT_2001c28c * 0x14) == 0) {
    piVar2 = (int *)(_DAT_2001c28c * 0x14 + 0x2001e8e8);
    do {
      piVar4 = piVar2;
      if (_DAT_2001c28c == 0) {
LAB_08011a50:
        bVar1 = (bool)isCurrentModePrivileged();
        if (bVar1) {
          setBasePriority(0x50);
        }
        InstructionSynchronizationBarrier(0xf);
        DataSynchronizationBarrier(0xf);
        do {
                    /* WARNING: Do nothing block with infinite loop */
        } while( true );
      }
      iVar3 = _DAT_2001c28c * 0x14;
      if (piVar4[5] != 0) {
        piVar4 = (int *)(iVar3 + 0x2001e8fc);
        _DAT_2001c28c = _DAT_2001c28c + -1;
        goto LAB_080119ea;
      }
      if (_DAT_2001c28c == 1) goto LAB_08011a50;
      if (*piVar4 != 0) {
        piVar4 = (int *)(iVar3 + 0x2001e8e8);
        _DAT_2001c28c = _DAT_2001c28c + -2;
        goto LAB_080119ea;
      }
      if (_DAT_2001c28c == 2) goto LAB_08011a50;
      if (piVar4[-5] != 0) {
        piVar4 = (int *)(iVar3 + 0x2001e8d4);
        _DAT_2001c28c = _DAT_2001c28c + -3;
        goto LAB_080119ea;
      }
      if (_DAT_2001c28c == 3) goto LAB_08011a50;
      _DAT_2001c28c = _DAT_2001c28c + -4;
      piVar2 = piVar4 + -0x14;
    } while (piVar4[-10] == 0);
    piVar4 = piVar4 + -10;
  }
LAB_080119ea:
  piVar2 = *(int **)(piVar4[1] + 4);
  piVar4[1] = (int)piVar2;
  if (piVar2 != piVar4 + 2) {
    _DAT_2001c268 = piVar2[3];
    return;
  }
  iVar3 = piVar2[1];
  piVar4[1] = iVar3;
  _DAT_2001c268 = *(undefined4 *)(iVar3 + 0xc);
  return;
}



/* 08011aa0 */

/* WARNING: Removing unreachable block (ram,0x08011adc) */
/* WARNING: Removing unreachable block (ram,0x08011ae0) */
/* WARNING: Removing unreachable block (ram,0x08011ae4) */
/* WARNING: Removing unreachable block (ram,0x08011aec) */

undefined4 * FUN_08011aa0(undefined4 *param_1)

{
  bool bVar1;
  
  if (param_1 != (undefined4 *)0x0) {
    *param_1 = 0;
    FUN_080112ac(param_1 + 1);
    *(undefined1 *)(param_1 + 7) = 1;
    return param_1;
  }
  bVar1 = (bool)isCurrentModePrivileged();
  if (bVar1) {
    setBasePriority(0x50);
  }
  InstructionSynchronizationBarrier(0xf);
  DataSynchronizationBarrier(0xf);
  do {
                    /* WARNING: Do nothing block with infinite loop */
  } while( true );
}



/* 08011af0 */

/* WARNING: Removing unreachable block (ram,0x08011c72) */
/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_08011af0(void)

{
  bool bVar1;
  int iVar2;
  int iVar3;
  int iVar4;
  char local_19;
  
  if (_DAT_e000ed00 == 0x410fc271) {
    bVar1 = (bool)isCurrentModePrivileged();
    if (bVar1) {
      setBasePriority(0x50);
    }
    InstructionSynchronizationBarrier(0xf);
    DataSynchronizationBarrier(0xf);
    do {
                    /* WARNING: Do nothing block with infinite loop */
    } while( true );
  }
  if (_DAT_e000ed00 == 0x410fc270) {
    bVar1 = (bool)isCurrentModePrivileged();
    if (bVar1) {
      setBasePriority(0x50);
    }
    InstructionSynchronizationBarrier(0xf);
    DataSynchronizationBarrier(0xf);
    do {
                    /* WARNING: Do nothing block with infinite loop */
    } while( true );
  }
  local_19 = -1;
  DAT_2001c33c = 0x50;
  iVar2 = 3;
  do {
    iVar3 = iVar2;
    iVar4 = iVar3 + 3;
    if ((((uint)(int)(char)(local_19 << 1) < 0x80000000) ||
        (iVar4 = iVar3 + 2, (uint)(int)(char)(local_19 << 2) < 0x80000000)) ||
       (iVar4 = iVar3 + 1, (uint)(int)(char)(local_19 << 3) < 0x80000000)) break;
    local_19 = local_19 << 4;
    iVar2 = iVar3 + -4;
    iVar4 = iVar3;
  } while (local_19 < '\0');
  if (iVar4 != 3) {
    bVar1 = (bool)isCurrentModePrivileged();
    if (bVar1) {
      setBasePriority(0x50);
    }
    InstructionSynchronizationBarrier(0xf);
    DataSynchronizationBarrier(0xf);
    do {
                    /* WARNING: Do nothing block with infinite loop */
    } while( true );
  }
  _DAT_2001c340 = 0x300;
  _DAT_e000ed20 = _DAT_e000ed20 | 0xf0f00000;
  FUN_080114b8();
  _DAT_2001c09c = 0;
  FUN_0801134c();
  _DAT_e000ef34 = _DAT_e000ef34 | 0xc0000000;
  FUN_0800e8c4();
  FUN_080119b0();
  bVar1 = (bool)isCurrentModePrivileged();
  if (bVar1) {
    setBasePriority(0x50);
  }
  InstructionSynchronizationBarrier(0xf);
  DataSynchronizationBarrier(0xf);
  if (_DAT_2001c09c != -1) {
    do {
                    /* WARNING: Do nothing block with infinite loop */
    } while( true );
  }
  do {
  } while( true );
}



/* 08011ca8 */

int * FUN_08011ca8(uint param_1,uint param_2)

{
  bool bVar1;
  int *piVar2;
  int iVar3;
  
  if (param_1 == 0) {
    bVar1 = (bool)isCurrentModePrivileged();
    if (bVar1) {
      setBasePriority(0x50);
    }
    InstructionSynchronizationBarrier(0xf);
    DataSynchronizationBarrier(0xf);
    do {
                    /* WARNING: Do nothing block with infinite loop */
    } while( true );
  }
  if (param_1 < param_2) {
    bVar1 = (bool)isCurrentModePrivileged();
    if (bVar1) {
      setBasePriority(0x50);
    }
    InstructionSynchronizationBarrier(0xf);
    DataSynchronizationBarrier(0xf);
    do {
                    /* WARNING: Do nothing block with infinite loop */
    } while( true );
  }
  piVar2 = (int *)FUN_0800ee94(0x50);
  if (piVar2 == (int *)0x0) {
    return (int *)0x0;
  }
  *(undefined1 *)((int)piVar2 + 0x46) = 0;
  *piVar2 = (int)piVar2;
  piVar2[0xf] = param_1;
  piVar2[0x10] = 0;
  FUN_08011360();
  iVar3 = *piVar2;
  piVar2[0xe] = 0;
  piVar2[1] = iVar3;
  piVar2[2] = piVar2[0x10] * piVar2[0xf] + iVar3;
  piVar2[3] = (piVar2[0xf] + -1) * piVar2[0x10] + iVar3;
  *(undefined1 *)(piVar2 + 0x11) = 0xff;
  *(undefined1 *)((int)piVar2 + 0x45) = 0xff;
  FUN_080112ac(piVar2 + 4);
  FUN_080112ac(piVar2 + 9);
  FUN_080113a8();
  *(undefined1 *)(piVar2 + 0x13) = 2;
  piVar2[0xe] = param_2;
  return piVar2;
}



/* 08011cd8 */

int * FUN_08011cd8(int param_1,int param_2)

{
  int *piVar1;
  int iVar2;
  
  piVar1 = (int *)FUN_0800ee94(0x50);
  if (piVar1 == (int *)0x0) {
    return (int *)0x0;
  }
  *(undefined1 *)((int)piVar1 + 0x46) = 0;
  *piVar1 = (int)piVar1;
  piVar1[0xf] = param_1;
  piVar1[0x10] = 0;
  FUN_08011360();
  iVar2 = *piVar1;
  piVar1[0xe] = 0;
  piVar1[1] = iVar2;
  piVar1[2] = piVar1[0x10] * piVar1[0xf] + iVar2;
  piVar1[3] = (piVar1[0xf] + -1) * piVar1[0x10] + iVar2;
  *(undefined1 *)(piVar1 + 0x11) = 0xff;
  *(undefined1 *)((int)piVar1 + 0x45) = 0xff;
  FUN_080112ac(piVar1 + 4);
  FUN_080112ac(piVar1 + 9);
  FUN_080113a8();
  *(undefined1 *)(piVar1 + 0x13) = 2;
  piVar1[0xe] = param_2;
  return piVar1;
}



/* 08011d40 */

/* WARNING: Removing unreachable block (ram,0x08011df0) */
/* WARNING: Removing unreachable block (ram,0x08011df4) */
/* WARNING: Removing unreachable block (ram,0x08011df8) */
/* WARNING: Removing unreachable block (ram,0x08011e00) */

int * FUN_08011d40(uint param_1,uint param_2,int *param_3)

{
  bool bVar1;
  int iVar2;
  
  if (param_1 == 0) {
    bVar1 = (bool)isCurrentModePrivileged();
    if (bVar1) {
      setBasePriority(0x50);
    }
    InstructionSynchronizationBarrier(0xf);
    DataSynchronizationBarrier(0xf);
    do {
                    /* WARNING: Do nothing block with infinite loop */
    } while( true );
  }
  if (param_2 <= param_1) {
    if (param_3 != (int *)0x0) {
      *(undefined1 *)((int)param_3 + 0x46) = 1;
      *param_3 = (int)param_3;
      param_3[0xf] = param_1;
      param_3[0x10] = 0;
      FUN_08011360();
      iVar2 = *param_3;
      param_3[0xe] = 0;
      param_3[1] = iVar2;
      param_3[2] = param_3[0x10] * param_3[0xf] + iVar2;
      param_3[3] = (param_3[0xf] + -1) * param_3[0x10] + iVar2;
      *(undefined1 *)(param_3 + 0x11) = 0xff;
      *(undefined1 *)((int)param_3 + 0x45) = 0xff;
      FUN_080112ac(param_3 + 4);
      FUN_080112ac(param_3 + 9);
      FUN_080113a8();
      *(undefined1 *)(param_3 + 0x13) = 2;
      param_3[0xe] = param_2;
      return param_3;
    }
    bVar1 = (bool)isCurrentModePrivileged();
    if (bVar1) {
      setBasePriority(0x50);
    }
    InstructionSynchronizationBarrier(0xf);
    DataSynchronizationBarrier(0xf);
    do {
                    /* WARNING: Do nothing block with infinite loop */
    } while( true );
  }
  bVar1 = (bool)isCurrentModePrivileged();
  if (bVar1) {
    setBasePriority(0x50);
  }
  InstructionSynchronizationBarrier(0xf);
  DataSynchronizationBarrier(0xf);
  do {
                    /* WARNING: Do nothing block with infinite loop */
  } while( true );
}



/* 08011e04 */

int * FUN_08011e04(undefined1 param_1)

{
  int *piVar1;
  int iVar2;
  
  piVar1 = (int *)FUN_0800ee94(0x50);
  if (piVar1 != (int *)0x0) {
    *(undefined1 *)((int)piVar1 + 0x46) = 0;
    *piVar1 = (int)piVar1;
    piVar1[0xf] = 1;
    piVar1[0x10] = 0;
    FUN_08011360();
    iVar2 = *piVar1;
    piVar1[0xe] = 0;
    piVar1[1] = iVar2;
    piVar1[2] = piVar1[0x10] * piVar1[0xf] + iVar2;
    piVar1[3] = (piVar1[0xf] + -1) * piVar1[0x10] + iVar2;
    *(undefined1 *)(piVar1 + 0x11) = 0xff;
    *(undefined1 *)((int)piVar1 + 0x45) = 0xff;
    FUN_080112ac(piVar1 + 4);
    FUN_080112ac(piVar1 + 9);
    FUN_080113a8();
    *(undefined1 *)(piVar1 + 0x13) = param_1;
    *piVar1 = 0;
    piVar1[2] = 0;
    piVar1[3] = 0;
    FUN_08012078(piVar1,0,0,0);
  }
  return piVar1;
}



/* 08011e74 */

/* WARNING: Removing unreachable block (ram,0x08011f04) */
/* WARNING: Removing unreachable block (ram,0x08011f08) */
/* WARNING: Removing unreachable block (ram,0x08011f0c) */
/* WARNING: Removing unreachable block (ram,0x08011f14) */

int * FUN_08011e74(undefined1 param_1,int *param_2)

{
  bool bVar1;
  int iVar2;
  
  if (param_2 != (int *)0x0) {
    *(undefined1 *)((int)param_2 + 0x46) = 1;
    *param_2 = (int)param_2;
    param_2[0xf] = 1;
    param_2[0x10] = 0;
    FUN_08011360();
    iVar2 = *param_2;
    param_2[0xe] = 0;
    param_2[1] = iVar2;
    param_2[2] = param_2[0x10] * param_2[0xf] + iVar2;
    param_2[3] = (param_2[0xf] + -1) * param_2[0x10] + iVar2;
    *(undefined1 *)(param_2 + 0x11) = 0xff;
    *(undefined1 *)((int)param_2 + 0x45) = 0xff;
    FUN_080112ac(param_2 + 4);
    FUN_080112ac(param_2 + 9);
    FUN_080113a8();
    *(undefined1 *)(param_2 + 0x13) = param_1;
    *param_2 = 0;
    param_2[2] = 0;
    param_2[3] = 0;
    FUN_08012078(param_2,0,0,0);
    return param_2;
  }
  bVar1 = (bool)isCurrentModePrivileged();
  if (bVar1) {
    setBasePriority(0x50);
  }
  InstructionSynchronizationBarrier(0xf);
  DataSynchronizationBarrier(0xf);
  do {
                    /* WARNING: Do nothing block with infinite loop */
  } while( true );
}



/* 08011f18 */

int * FUN_08011f18(int param_1,int param_2,undefined1 param_3)

{
  bool bVar1;
  int *piVar2;
  int iVar3;
  int *piVar4;
  
  if (param_1 != 0) {
    piVar2 = (int *)FUN_0800ee94(param_2 * param_1 + 0x50);
    if (piVar2 != (int *)0x0) {
      *(undefined1 *)((int)piVar2 + 0x46) = 0;
      piVar4 = piVar2;
      if (param_2 != 0) {
        piVar4 = piVar2 + 0x14;
      }
      *piVar2 = (int)piVar4;
      piVar2[0xf] = param_1;
      piVar2[0x10] = param_2;
      FUN_08011360();
      iVar3 = *piVar2;
      piVar2[0xe] = 0;
      piVar2[1] = iVar3;
      piVar2[2] = piVar2[0x10] * piVar2[0xf] + iVar3;
      piVar2[3] = (piVar2[0xf] + -1) * piVar2[0x10] + iVar3;
      *(undefined1 *)(piVar2 + 0x11) = 0xff;
      *(undefined1 *)((int)piVar2 + 0x45) = 0xff;
      FUN_080112ac(piVar2 + 4);
      FUN_080112ac(piVar2 + 9);
      FUN_080113a8();
      *(undefined1 *)(piVar2 + 0x13) = param_3;
    }
    return piVar2;
  }
  bVar1 = (bool)isCurrentModePrivileged();
  if (bVar1) {
    setBasePriority(0x50);
  }
  InstructionSynchronizationBarrier(0xf);
  DataSynchronizationBarrier(0xf);
  do {
                    /* WARNING: Do nothing block with infinite loop */
  } while( true );
}



/* 08011f9c */

/* WARNING: Removing unreachable block (ram,0x08012064) */
/* WARNING: Removing unreachable block (ram,0x08012068) */
/* WARNING: Removing unreachable block (ram,0x0801206c) */
/* WARNING: Removing unreachable block (ram,0x08012074) */

int * FUN_08011f9c(int param_1,int param_2,int *param_3,int *param_4,undefined1 param_5)

{
  bool bVar1;
  int iVar2;
  
  if (param_1 == 0) {
    bVar1 = (bool)isCurrentModePrivileged();
    if (bVar1) {
      setBasePriority(0x50);
    }
    InstructionSynchronizationBarrier(0xf);
    DataSynchronizationBarrier(0xf);
    do {
                    /* WARNING: Do nothing block with infinite loop */
    } while( true );
  }
  if (param_4 == (int *)0x0) {
    bVar1 = (bool)isCurrentModePrivileged();
    if (bVar1) {
      setBasePriority(0x50);
    }
    InstructionSynchronizationBarrier(0xf);
    DataSynchronizationBarrier(0xf);
    do {
                    /* WARNING: Do nothing block with infinite loop */
    } while( true );
  }
  if ((param_2 == 0) && (param_3 != (int *)0x0)) {
    bVar1 = (bool)isCurrentModePrivileged();
    if (bVar1) {
      setBasePriority(0x50);
    }
    InstructionSynchronizationBarrier(0xf);
    DataSynchronizationBarrier(0xf);
    do {
                    /* WARNING: Do nothing block with infinite loop */
    } while( true );
  }
  if ((param_2 != 0) && (param_3 == (int *)0x0)) {
    bVar1 = (bool)isCurrentModePrivileged();
    if (bVar1) {
      setBasePriority(0x50);
    }
    InstructionSynchronizationBarrier(0xf);
    DataSynchronizationBarrier(0xf);
    do {
                    /* WARNING: Do nothing block with infinite loop */
    } while( true );
  }
  *(undefined1 *)((int)param_4 + 0x46) = 1;
  if (param_2 == 0) {
    param_3 = param_4;
  }
  *param_4 = (int)param_3;
  param_4[0xf] = param_1;
  param_4[0x10] = param_2;
  FUN_08011360();
  iVar2 = *param_4;
  param_4[0xe] = 0;
  param_4[1] = iVar2;
  param_4[2] = param_4[0x10] * param_4[0xf] + iVar2;
  param_4[3] = (param_4[0xf] + -1) * param_4[0x10] + iVar2;
  *(undefined1 *)(param_4 + 0x11) = 0xff;
  *(undefined1 *)((int)param_4 + 0x45) = 0xff;
  FUN_080112ac(param_4 + 4);
  FUN_080112ac(param_4 + 9);
  FUN_080113a8();
  *(undefined1 *)(param_4 + 0x13) = param_5;
  return param_4;
}



/* 08012078 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined4 FUN_08012078(uint *param_1,int param_2,int param_3,int param_4)

{
  bool bVar1;
  int iVar2;
  uint uVar3;
  uint uVar4;
  undefined1 auStack_30 [8];
  int local_28;
  
  if (param_1 == (uint *)0x0) {
    bVar1 = (bool)isCurrentModePrivileged();
    if (bVar1) {
      setBasePriority(0x50);
    }
    InstructionSynchronizationBarrier(0xf);
    DataSynchronizationBarrier(0xf);
    do {
                    /* WARNING: Do nothing block with infinite loop */
    } while( true );
  }
  if ((param_2 == 0) && (param_1[0x10] != 0)) {
    bVar1 = (bool)isCurrentModePrivileged();
    if (bVar1) {
      setBasePriority(0x50);
    }
    InstructionSynchronizationBarrier(0xf);
    DataSynchronizationBarrier(0xf);
    do {
                    /* WARNING: Do nothing block with infinite loop */
    } while( true );
  }
  if ((param_4 == 2) && (param_1[0xf] != 1)) {
    bVar1 = (bool)isCurrentModePrivileged();
    if (bVar1) {
      setBasePriority(0x50);
    }
    InstructionSynchronizationBarrier(0xf);
    DataSynchronizationBarrier(0xf);
    do {
                    /* WARNING: Do nothing block with infinite loop */
    } while( true );
  }
  local_28 = param_3;
  iVar2 = FUN_08012ce8();
  if ((iVar2 == 0) && (param_3 != 0)) {
    bVar1 = (bool)isCurrentModePrivileged();
    if (bVar1) {
      setBasePriority(0x50);
    }
    InstructionSynchronizationBarrier(0xf);
    DataSynchronizationBarrier(0xf);
    do {
                    /* WARNING: Do nothing block with infinite loop */
    } while( true );
  }
  FUN_08011360();
  if ((param_4 != 2) && (param_1[0xf] <= param_1[0xe])) {
    if (local_28 == 0) {
LAB_0801232c:
      FUN_080113a8();
      return 0;
    }
    FUN_080116f8(auStack_30);
    FUN_080113a8();
    FUN_080119a0();
    FUN_08011360();
    if ((char)param_1[0x11] == -1) {
      *(undefined1 *)(param_1 + 0x11) = 0;
    }
    if (*(char *)((int)param_1 + 0x45) == -1) {
      *(undefined1 *)((int)param_1 + 0x45) = 0;
    }
    FUN_080113a8();
    iVar2 = FUN_08012b68(auStack_30,&local_28);
    if (iVar2 != 0) {
LAB_08012138:
      FUN_0800eca8(param_1);
      FUN_08012fd0();
      return 0;
    }
    FUN_08011360();
    uVar4 = param_1[0xe];
    uVar3 = param_1[0xf];
    FUN_080113a8();
    if (uVar4 == uVar3) {
      FUN_0801171c(param_1 + 4,local_28);
      FUN_0800eca8(param_1);
      iVar2 = FUN_08012fd0();
      if (iVar2 == 0) {
        _DAT_e000ed04 = 0x10000000;
        DataSynchronizationBarrier(0xf);
        InstructionSynchronizationBarrier(0xf);
      }
    }
    else {
      FUN_0800eca8(param_1);
      FUN_08012fd0();
    }
    FUN_08011360();
    if (param_1[0xf] <= param_1[0xe]) {
      do {
        if (local_28 == 0) goto LAB_0801232c;
        FUN_080113a8();
        FUN_080119a0();
        FUN_08011360();
        if ((char)param_1[0x11] == -1) {
          *(undefined1 *)(param_1 + 0x11) = 0;
        }
        if (*(char *)((int)param_1 + 0x45) == -1) {
          *(undefined1 *)((int)param_1 + 0x45) = 0;
        }
        FUN_080113a8();
        iVar2 = FUN_08012b68(auStack_30,&local_28);
        if (iVar2 != 0) goto LAB_08012138;
        FUN_08011360();
        uVar3 = param_1[0xe];
        uVar4 = param_1[0xf];
        FUN_080113a8();
        if (uVar3 == uVar4) {
          FUN_0801171c(param_1 + 4,local_28);
          FUN_0800eca8(param_1);
          iVar2 = FUN_08012fd0();
          if (iVar2 == 0) {
            _DAT_e000ed04 = 0x10000000;
            DataSynchronizationBarrier(0xf);
            InstructionSynchronizationBarrier(0xf);
          }
        }
        else {
          FUN_0800eca8(param_1);
          FUN_08012fd0();
        }
        FUN_08011360();
      } while (param_1[0xf] <= param_1[0xe]);
    }
  }
  uVar3 = param_1[0xe];
  if (param_1[0x10] == 0) {
    if (*param_1 == 0) {
      iVar2 = FUN_08012e3c(param_1[2]);
      param_1[2] = 0;
      bVar1 = iVar2 == 0;
      goto LAB_0801222a;
    }
  }
  else if (param_4 == 0) {
    FUN_080006aa(param_1[1],param_2);
    uVar4 = param_1[1];
    param_1[1] = uVar4 + param_1[0x10];
    if (param_1[2] <= uVar4 + param_1[0x10]) {
      param_1[1] = *param_1;
    }
  }
  else {
    FUN_080006aa(param_1[3],param_2);
    uVar4 = param_1[3] - param_1[0x10];
    param_1[3] = uVar4;
    if (uVar4 < *param_1) {
      param_1[3] = param_1[2] - param_1[0x10];
    }
    uVar3 = uVar3 - (param_4 == 2 && uVar3 != 0);
  }
  bVar1 = true;
LAB_0801222a:
  param_1[0xe] = uVar3 + 1;
  if (param_1[9] == 0) {
    if (!bVar1) {
      _DAT_e000ed04 = 0x10000000;
      DataSynchronizationBarrier(0xf);
      InstructionSynchronizationBarrier(0xf);
      FUN_080113a8();
      return 1;
    }
  }
  else {
    iVar2 = FUN_08012f5c(param_1 + 9);
    if (iVar2 != 0) {
      _DAT_e000ed04 = 0x10000000;
      DataSynchronizationBarrier(0xf);
      InstructionSynchronizationBarrier(0xf);
    }
  }
  FUN_080113a8();
  return 1;
}



/* 08012338 */

undefined4 FUN_08012338(uint *param_1,int param_2,undefined4 *param_3,int param_4)

{
  char cVar1;
  bool bVar2;
  int iVar3;
  uint uVar4;
  uint uVar5;
  undefined4 uVar6;
  
  if (param_1 == (uint *)0x0) {
    bVar2 = (bool)isCurrentModePrivileged();
    if (bVar2) {
      setBasePriority(0x50);
    }
    InstructionSynchronizationBarrier(0xf);
    DataSynchronizationBarrier(0xf);
    do {
                    /* WARNING: Do nothing block with infinite loop */
    } while( true );
  }
  if ((param_2 == 0) && (param_1[0x10] != 0)) {
    bVar2 = (bool)isCurrentModePrivileged();
    if (bVar2) {
      setBasePriority(0x50);
    }
    InstructionSynchronizationBarrier(0xf);
    DataSynchronizationBarrier(0xf);
    do {
                    /* WARNING: Do nothing block with infinite loop */
    } while( true );
  }
  if ((param_4 == 2) && (param_1[0xf] != 1)) {
    bVar2 = (bool)isCurrentModePrivileged();
    if (bVar2) {
      setBasePriority(0x50);
    }
    InstructionSynchronizationBarrier(0xf);
    DataSynchronizationBarrier(0xf);
    do {
                    /* WARNING: Do nothing block with infinite loop */
    } while( true );
  }
  FUN_080114ec();
  uVar6 = 0;
  bVar2 = (bool)isCurrentModePrivileged();
  if (bVar2) {
    uVar6 = getBasePriority();
  }
  bVar2 = (bool)isCurrentModePrivileged();
  if (bVar2) {
    setBasePriority(0x50);
  }
  InstructionSynchronizationBarrier(0xf);
  DataSynchronizationBarrier(0xf);
  if ((param_4 != 2) && (param_1[0xf] <= param_1[0xe])) {
    bVar2 = (bool)isCurrentModePrivileged();
    if (bVar2) {
      setBasePriority(uVar6);
    }
    return 0;
  }
  cVar1 = *(char *)((int)param_1 + 0x45);
  uVar5 = param_1[0xe];
  if (param_1[0x10] == 0) {
    if (*param_1 == 0) {
      FUN_08012e3c(param_1[2]);
      param_1[2] = 0;
    }
  }
  else if (param_4 == 0) {
    FUN_080006aa(param_1[1],param_2);
    uVar4 = param_1[1];
    param_1[1] = uVar4 + param_1[0x10];
    if (param_1[2] <= uVar4 + param_1[0x10]) {
      param_1[1] = *param_1;
    }
  }
  else {
    FUN_080006aa(param_1[3],param_2);
    uVar4 = param_1[3] - param_1[0x10];
    param_1[3] = uVar4;
    if (uVar4 < *param_1) {
      param_1[3] = param_1[2] - param_1[0x10];
    }
    uVar5 = uVar5 - (param_4 == 2 && uVar5 != 0);
  }
  param_1[0xe] = uVar5 + 1;
  if (cVar1 == -1) {
    if (param_1[9] != 0) {
      iVar3 = FUN_08012f5c(param_1 + 9);
      if (param_3 == (undefined4 *)0x0 || iVar3 == 0) {
        bVar2 = (bool)isCurrentModePrivileged();
        if (bVar2) {
          setBasePriority(uVar6);
        }
        return 1;
      }
      *param_3 = 1;
      bVar2 = (bool)isCurrentModePrivileged();
      if (bVar2) {
        setBasePriority(uVar6);
      }
      return 1;
    }
  }
  else {
    *(char *)((int)param_1 + 0x45) = cVar1 + '\x01';
  }
  bVar2 = (bool)isCurrentModePrivileged();
  if (bVar2) {
    setBasePriority(uVar6);
  }
  return 1;
}



/* 08012480 */

undefined4 FUN_08012480(int *param_1,undefined4 *param_2)

{
  bool bVar1;
  int iVar2;
  undefined4 uVar3;
  
  if (param_1 == (int *)0x0) {
    bVar1 = (bool)isCurrentModePrivileged();
    if (bVar1) {
      setBasePriority(0x50);
    }
    InstructionSynchronizationBarrier(0xf);
    DataSynchronizationBarrier(0xf);
    do {
                    /* WARNING: Do nothing block with infinite loop */
    } while( true );
  }
  if (param_1[0x10] != 0) {
    bVar1 = (bool)isCurrentModePrivileged();
    if (bVar1) {
      setBasePriority(0x50);
    }
    InstructionSynchronizationBarrier(0xf);
    DataSynchronizationBarrier(0xf);
    do {
                    /* WARNING: Do nothing block with infinite loop */
    } while( true );
  }
  if ((*param_1 == 0) && (param_1[2] != 0)) {
    bVar1 = (bool)isCurrentModePrivileged();
    if (bVar1) {
      setBasePriority(0x50);
    }
    InstructionSynchronizationBarrier(0xf);
    DataSynchronizationBarrier(0xf);
    do {
                    /* WARNING: Do nothing block with infinite loop */
    } while( true );
  }
  FUN_080114ec();
  uVar3 = 0;
  bVar1 = (bool)isCurrentModePrivileged();
  if (bVar1) {
    uVar3 = getBasePriority();
  }
  bVar1 = (bool)isCurrentModePrivileged();
  if (bVar1) {
    setBasePriority(0x50);
  }
  InstructionSynchronizationBarrier(0xf);
  DataSynchronizationBarrier(0xf);
  if ((uint)param_1[0xf] <= (uint)param_1[0xe]) {
    bVar1 = (bool)isCurrentModePrivileged();
    if (bVar1) {
      setBasePriority(uVar3);
    }
    return 0;
  }
  param_1[0xe] = param_1[0xe] + 1;
  if (*(char *)((int)param_1 + 0x45) == -1) {
    if ((param_1[9] != 0) &&
       (iVar2 = FUN_08012f5c(param_1 + 9), param_2 != (undefined4 *)0x0 && iVar2 != 0)) {
      *param_2 = 1;
      bVar1 = (bool)isCurrentModePrivileged();
      if (bVar1) {
        setBasePriority(uVar3);
      }
      return 1;
    }
  }
  else {
    *(char *)((int)param_1 + 0x45) = *(char *)((int)param_1 + 0x45) + '\x01';
  }
  bVar1 = (bool)isCurrentModePrivileged();
  if (bVar1) {
    setBasePriority(uVar3);
  }
  return 1;
}



/* 0801253c */

undefined4 FUN_0801253c(int param_1)

{
  bool bVar1;
  int iVar2;
  int iVar3;
  
  if (param_1 == 0) {
    bVar1 = (bool)isCurrentModePrivileged();
    if (bVar1) {
      setBasePriority(0x50);
    }
    InstructionSynchronizationBarrier(0xf);
    DataSynchronizationBarrier(0xf);
    do {
                    /* WARNING: Do nothing block with infinite loop */
    } while( true );
  }
  iVar3 = *(int *)(param_1 + 8);
  iVar2 = FUN_08012cdc();
  if (iVar3 == iVar2) {
    iVar2 = *(int *)(param_1 + 0xc) + -1;
    *(int *)(param_1 + 0xc) = iVar2;
    if (iVar2 == 0) {
      FUN_08012078(param_1,0,0,0);
      return 1;
    }
    return 1;
  }
  return 0;
}



/* 08012580 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined4 FUN_08012580(undefined4 *param_1,int param_2,int param_3)

{
  bool bVar1;
  int iVar2;
  uint uVar3;
  undefined1 auStack_30 [8];
  int local_28;
  
  if (param_1 == (undefined4 *)0x0) {
    bVar1 = (bool)isCurrentModePrivileged();
    if (bVar1) {
      setBasePriority(0x50);
    }
    InstructionSynchronizationBarrier(0xf);
    DataSynchronizationBarrier(0xf);
    do {
                    /* WARNING: Do nothing block with infinite loop */
    } while( true );
  }
  if ((param_2 == 0) && (param_1[0x10] != 0)) {
    bVar1 = (bool)isCurrentModePrivileged();
    if (bVar1) {
      setBasePriority(0x50);
    }
    InstructionSynchronizationBarrier(0xf);
    DataSynchronizationBarrier(0xf);
    do {
                    /* WARNING: Do nothing block with infinite loop */
    } while( true );
  }
  local_28 = param_3;
  iVar2 = FUN_08012ce8();
  if ((iVar2 == 0) && (param_3 != 0)) {
    bVar1 = (bool)isCurrentModePrivileged();
    if (bVar1) {
      setBasePriority(0x50);
    }
    InstructionSynchronizationBarrier(0xf);
    DataSynchronizationBarrier(0xf);
    do {
                    /* WARNING: Do nothing block with infinite loop */
    } while( true );
  }
  FUN_08011360();
  iVar2 = param_1[0xe];
  if (iVar2 == 0) {
    if (local_28 == 0) {
LAB_080127b0:
      FUN_080113a8();
      return 0;
    }
    FUN_080116f8(auStack_30);
    FUN_080113a8();
    FUN_080119a0();
    FUN_08011360();
    if (*(char *)(param_1 + 0x11) == -1) {
      *(undefined1 *)(param_1 + 0x11) = 0;
    }
    if (*(char *)((int)param_1 + 0x45) == -1) {
      *(undefined1 *)((int)param_1 + 0x45) = 0;
    }
    FUN_080113a8();
    iVar2 = FUN_08012b68(auStack_30,&local_28);
    if (iVar2 == 0) {
      FUN_08011360();
      iVar2 = param_1[0xe];
      FUN_080113a8();
      if (iVar2 == 0) {
        FUN_0801171c(param_1 + 9,local_28);
        FUN_0800eca8(param_1);
        iVar2 = FUN_08012fd0();
        if (iVar2 == 0) {
          _DAT_e000ed04 = 0x10000000;
          DataSynchronizationBarrier(0xf);
          InstructionSynchronizationBarrier(0xf);
        }
      }
      else {
        FUN_0800eca8(param_1);
        FUN_08012fd0();
      }
    }
    else {
      FUN_0800eca8(param_1);
      FUN_08012fd0();
      FUN_08011360();
      iVar2 = param_1[0xe];
      FUN_080113a8();
      if (iVar2 == 0) {
        return 0;
      }
    }
    FUN_08011360();
    iVar2 = param_1[0xe];
    if (iVar2 == 0) {
      do {
        if (local_28 == 0) goto LAB_080127b0;
        FUN_080113a8();
        FUN_080119a0();
        FUN_08011360();
        if (*(char *)(param_1 + 0x11) == -1) {
          *(undefined1 *)(param_1 + 0x11) = 0;
        }
        if (*(char *)((int)param_1 + 0x45) == -1) {
          *(undefined1 *)((int)param_1 + 0x45) = 0;
        }
        FUN_080113a8();
        iVar2 = FUN_08012b68(auStack_30,&local_28);
        if (iVar2 == 0) {
          FUN_08011360();
          iVar2 = param_1[0xe];
          FUN_080113a8();
          if (iVar2 == 0) {
            FUN_0801171c(param_1 + 9,local_28);
            FUN_0800eca8(param_1);
            iVar2 = FUN_08012fd0();
            if (iVar2 == 0) {
              _DAT_e000ed04 = 0x10000000;
              DataSynchronizationBarrier(0xf);
              InstructionSynchronizationBarrier(0xf);
            }
          }
          else {
            FUN_0800eca8(param_1);
            FUN_08012fd0();
          }
        }
        else {
          FUN_0800eca8(param_1);
          FUN_08012fd0();
          FUN_08011360();
          iVar2 = param_1[0xe];
          FUN_080113a8();
          if (iVar2 == 0) {
            return 0;
          }
        }
        FUN_08011360();
        iVar2 = param_1[0xe];
      } while (iVar2 == 0);
    }
  }
  if (param_1[0x10] != 0) {
    uVar3 = param_1[3] + param_1[0x10];
    param_1[3] = uVar3;
    if ((uint)param_1[2] <= uVar3) {
      param_1[3] = *param_1;
    }
    FUN_080006aa(param_2);
  }
  param_1[0xe] = iVar2 + -1;
  if ((param_1[4] != 0) && (iVar2 = FUN_08012f5c(param_1 + 4), iVar2 != 0)) {
    _DAT_e000ed04 = 0x10000000;
    DataSynchronizationBarrier(0xf);
    InstructionSynchronizationBarrier(0xf);
  }
  FUN_080113a8();
  return 1;
}



/* 080127c0 */

undefined4 FUN_080127c0(undefined4 *param_1,int param_2,undefined4 *param_3)

{
  char cVar1;
  bool bVar2;
  uint uVar3;
  int iVar4;
  undefined4 uVar5;
  
  if (param_1 == (undefined4 *)0x0) {
    bVar2 = (bool)isCurrentModePrivileged();
    if (bVar2) {
      setBasePriority(0x50);
    }
    InstructionSynchronizationBarrier(0xf);
    DataSynchronizationBarrier(0xf);
    do {
                    /* WARNING: Do nothing block with infinite loop */
    } while( true );
  }
  if ((param_2 == 0) && (param_1[0x10] != 0)) {
    bVar2 = (bool)isCurrentModePrivileged();
    if (bVar2) {
      setBasePriority(0x50);
    }
    InstructionSynchronizationBarrier(0xf);
    DataSynchronizationBarrier(0xf);
    do {
                    /* WARNING: Do nothing block with infinite loop */
    } while( true );
  }
  FUN_080114ec();
  uVar5 = 0;
  bVar2 = (bool)isCurrentModePrivileged();
  if (bVar2) {
    uVar5 = getBasePriority();
  }
  bVar2 = (bool)isCurrentModePrivileged();
  if (bVar2) {
    setBasePriority(0x50);
  }
  InstructionSynchronizationBarrier(0xf);
  DataSynchronizationBarrier(0xf);
  iVar4 = param_1[0xe];
  if (iVar4 == 0) {
    bVar2 = (bool)isCurrentModePrivileged();
    if (bVar2) {
      setBasePriority(uVar5);
    }
    return 0;
  }
  cVar1 = *(char *)(param_1 + 0x11);
  if (param_1[0x10] != 0) {
    uVar3 = param_1[3] + param_1[0x10];
    param_1[3] = uVar3;
    if ((uint)param_1[2] <= uVar3) {
      param_1[3] = *param_1;
    }
    FUN_080006aa(param_2);
  }
  param_1[0xe] = iVar4 + -1;
  if (cVar1 == -1) {
    if (param_1[4] != 0) {
      iVar4 = FUN_08012f5c(param_1 + 4);
      if ((param_3 != (undefined4 *)0x0) && (iVar4 != 0)) {
        *param_3 = 1;
      }
      bVar2 = (bool)isCurrentModePrivileged();
      if (bVar2) {
        setBasePriority(uVar5);
      }
      return 1;
    }
  }
  else {
    *(char *)(param_1 + 0x11) = cVar1 + '\x01';
  }
  bVar2 = (bool)isCurrentModePrivileged();
  if (bVar2) {
    setBasePriority(uVar5);
  }
  return 1;
}



/* 08012894 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined4 FUN_08012894(int *param_1,int param_2)

{
  bool bVar1;
  int iVar2;
  int iVar3;
  int *piVar4;
  undefined1 auStack_30 [8];
  int local_28;
  
  if (param_1 == (int *)0x0) {
    bVar1 = (bool)isCurrentModePrivileged();
    if (bVar1) {
      setBasePriority(0x50);
    }
    InstructionSynchronizationBarrier(0xf);
    DataSynchronizationBarrier(0xf);
    do {
                    /* WARNING: Do nothing block with infinite loop */
    } while( true );
  }
  if (param_1[0x10] != 0) {
    bVar1 = (bool)isCurrentModePrivileged();
    if (bVar1) {
      setBasePriority(0x50);
    }
    InstructionSynchronizationBarrier(0xf);
    DataSynchronizationBarrier(0xf);
    do {
                    /* WARNING: Do nothing block with infinite loop */
    } while( true );
  }
  local_28 = param_2;
  iVar2 = FUN_08012ce8();
  if ((iVar2 == 0) && (param_2 != 0)) {
    bVar1 = (bool)isCurrentModePrivileged();
    if (bVar1) {
      setBasePriority(0x50);
    }
    InstructionSynchronizationBarrier(0xf);
    DataSynchronizationBarrier(0xf);
    do {
                    /* WARNING: Do nothing block with infinite loop */
    } while( true );
  }
  FUN_08011360();
  iVar2 = param_1[0xe];
  if (iVar2 == 0) {
    if (local_28 == 0) {
LAB_08012b10:
      FUN_080113a8();
      return 0;
    }
    FUN_080116f8(auStack_30);
    FUN_080113a8();
    FUN_080119a0();
    FUN_08011360();
    piVar4 = param_1 + 9;
    if ((char)param_1[0x11] == -1) {
      *(undefined1 *)(param_1 + 0x11) = 0;
    }
    if (*(char *)((int)param_1 + 0x45) == -1) {
      *(undefined1 *)((int)param_1 + 0x45) = 0;
    }
    FUN_080113a8();
    iVar2 = FUN_08012b68(auStack_30,&local_28);
    if (iVar2 == 0) {
      FUN_08011360();
      iVar2 = param_1[0xe];
      FUN_080113a8();
      if (iVar2 == 0) {
        if (*param_1 == 0) {
          FUN_08011360();
          iVar3 = FUN_08012ecc(param_1[2]);
          FUN_080113a8();
        }
        else {
          iVar3 = 0;
        }
        FUN_0801171c(piVar4,local_28);
        FUN_0800eca8(param_1);
        iVar2 = FUN_08012fd0();
        if (iVar2 == 0) {
          _DAT_e000ed04 = 0x10000000;
          DataSynchronizationBarrier(0xf);
          InstructionSynchronizationBarrier(0xf);
        }
      }
      else {
        FUN_0800eca8(param_1);
        FUN_08012fd0();
        iVar3 = 0;
      }
    }
    else {
      FUN_0800eca8(param_1);
      FUN_08012fd0();
      FUN_08011360();
      iVar2 = param_1[0xe];
      FUN_080113a8();
      iVar3 = 0;
      if (iVar2 == 0) {
        return 0;
      }
    }
    FUN_08011360();
    iVar2 = param_1[0xe];
    if (iVar2 == 0) {
      do {
        if (local_28 == 0) {
          if (iVar3 != 0) {
            bVar1 = (bool)isCurrentModePrivileged();
            if (bVar1) {
              setBasePriority(0x50);
            }
            InstructionSynchronizationBarrier(0xf);
            DataSynchronizationBarrier(0xf);
            do {
                    /* WARNING: Do nothing block with infinite loop */
            } while( true );
          }
          goto LAB_08012b10;
        }
        FUN_080113a8();
        FUN_080119a0();
        FUN_08011360();
        if ((char)param_1[0x11] == -1) {
          *(undefined1 *)(param_1 + 0x11) = 0;
        }
        if (*(char *)((int)param_1 + 0x45) == -1) {
          *(undefined1 *)((int)param_1 + 0x45) = 0;
        }
        FUN_080113a8();
        iVar2 = FUN_08012b68(auStack_30,&local_28);
        if (iVar2 == 0) {
          FUN_08011360();
          iVar2 = param_1[0xe];
          FUN_080113a8();
          if (iVar2 == 0) {
            if (*param_1 == 0) {
              FUN_08011360();
              iVar3 = FUN_08012ecc(param_1[2]);
              FUN_080113a8();
            }
            FUN_0801171c(piVar4,local_28);
            FUN_0800eca8(param_1);
            iVar2 = FUN_08012fd0();
            if (iVar2 == 0) {
              _DAT_e000ed04 = 0x10000000;
              DataSynchronizationBarrier(0xf);
              InstructionSynchronizationBarrier(0xf);
            }
          }
          else {
            FUN_0800eca8(param_1);
            FUN_08012fd0();
          }
        }
        else {
          FUN_0800eca8(param_1);
          FUN_08012fd0();
          FUN_08011360();
          iVar2 = param_1[0xe];
          FUN_080113a8();
          if (iVar2 == 0) {
            if (iVar3 == 0) {
              return 0;
            }
            FUN_08011360();
            if (*piVar4 == 0) {
              iVar2 = 0;
            }
            else {
              iVar2 = 0x38 - *(int *)param_1[0xc];
            }
            FUN_0801180c(param_1[2],iVar2);
            goto LAB_08012b10;
          }
        }
        FUN_08011360();
        iVar2 = param_1[0xe];
      } while (iVar2 == 0);
    }
  }
  param_1[0xe] = iVar2 + -1;
  if (*param_1 == 0) {
    iVar2 = FUN_0800f07c();
    param_1[2] = iVar2;
  }
  if ((param_1[4] != 0) && (iVar2 = FUN_08012f5c(param_1 + 4), iVar2 != 0)) {
    _DAT_e000ed04 = 0x10000000;
    DataSynchronizationBarrier(0xf);
    InstructionSynchronizationBarrier(0xf);
  }
  FUN_080113a8();
  return 1;
}



/* 08012b20 */

int FUN_08012b20(int param_1,undefined4 param_2)

{
  bool bVar1;
  int iVar2;
  int iVar3;
  
  if (param_1 == 0) {
    bVar1 = (bool)isCurrentModePrivileged();
    if (bVar1) {
      setBasePriority(0x50);
    }
    InstructionSynchronizationBarrier(0xf);
    DataSynchronizationBarrier(0xf);
    do {
                    /* WARNING: Do nothing block with infinite loop */
    } while( true );
  }
  iVar3 = *(int *)(param_1 + 8);
  iVar2 = FUN_08012cdc();
  if (iVar3 != iVar2) {
    iVar2 = FUN_08012894(param_1,param_2);
    if (iVar2 != 0) {
      *(int *)(param_1 + 0xc) = *(int *)(param_1 + 0xc) + 1;
      return iVar2;
    }
    return 0;
  }
  *(int *)(param_1 + 0xc) = *(int *)(param_1 + 0xc) + 1;
  return 1;
}



/* 08012b68 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined4 FUN_08012b68(int *param_1,uint *param_2)

{
  bool bVar1;
  uint uVar2;
  uint uVar3;
  
  if (param_1 == (int *)0x0) {
    bVar1 = (bool)isCurrentModePrivileged();
    if (bVar1) {
      setBasePriority(0x50);
    }
    InstructionSynchronizationBarrier(0xf);
    DataSynchronizationBarrier(0xf);
    do {
                    /* WARNING: Do nothing block with infinite loop */
    } while( true );
  }
  if (param_2 != (uint *)0x0) {
    FUN_08011360();
    uVar3 = *param_2;
    if (uVar3 == 0xffffffff) {
      FUN_080113a8();
      return 0;
    }
    if ((_DAT_2001c2a0 == *param_1) || (_DAT_2001c280 < (uint)param_1[1])) {
      uVar2 = _DAT_2001c280 - param_1[1];
      if (uVar2 < uVar3) {
        *param_2 = uVar3 - uVar2;
        *param_1 = _DAT_2001c2a0;
        param_1[1] = _DAT_2001c280;
        FUN_080113a8();
        return 0;
      }
      *param_2 = 0;
    }
    FUN_080113a8();
    return 1;
  }
  bVar1 = (bool)isCurrentModePrivileged();
  if (bVar1) {
    setBasePriority(0x50);
  }
  InstructionSynchronizationBarrier(0xf);
  DataSynchronizationBarrier(0xf);
  do {
                    /* WARNING: Do nothing block with infinite loop */
  } while( true );
}



/* 08012c04 */

undefined4
FUN_08012c04(undefined4 param_1,undefined4 param_2,int param_3,undefined4 param_4,undefined4 param_5
            ,undefined4 param_6)

{
  int iVar1;
  int iVar2;
  
  iVar1 = FUN_0800ee94(param_3 << 2);
  if (iVar1 != 0) {
    iVar2 = FUN_0800ee94(0x5c);
    if (iVar2 != 0) {
      *(int *)(iVar2 + 0x30) = iVar1;
      *(undefined1 *)(iVar2 + 0x59) = 0;
      FUN_0800e710(param_1,param_2,param_3,param_4,param_5,param_6,iVar2);
      FUN_0800e3f8(iVar2);
      return 1;
    }
    FUN_080113d8(iVar1);
  }
  return 0xffffffff;
}



/* 08012c64 */

/* WARNING: Removing unreachable block (ram,0x08012cc8) */
/* WARNING: Removing unreachable block (ram,0x08012ccc) */
/* WARNING: Removing unreachable block (ram,0x08012cd0) */
/* WARNING: Removing unreachable block (ram,0x08012cd8) */

undefined4 FUN_08012c64(void)

{
  bool bVar1;
  int in_stack_00000004;
  int in_stack_00000008;
  undefined4 local_14;
  
  if (in_stack_00000004 == 0) {
    bVar1 = (bool)isCurrentModePrivileged();
    if (bVar1) {
      setBasePriority(0x50);
    }
    InstructionSynchronizationBarrier(0xf);
    DataSynchronizationBarrier(0xf);
    do {
                    /* WARNING: Do nothing block with infinite loop */
    } while( true );
  }
  if (in_stack_00000008 == 0) {
    bVar1 = (bool)isCurrentModePrivileged();
    if (bVar1) {
      setBasePriority(0x50);
    }
    InstructionSynchronizationBarrier(0xf);
    DataSynchronizationBarrier(0xf);
    do {
                    /* WARNING: Do nothing block with infinite loop */
    } while( true );
  }
  *(undefined1 *)(in_stack_00000008 + 0x59) = 2;
  *(int *)(in_stack_00000008 + 0x30) = in_stack_00000004;
  FUN_0800e710();
  FUN_0800e3f8(in_stack_00000008);
  return local_14;
}



/* 08012cdc */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined4 FUN_08012cdc(void)

{
  return _DAT_2001c268;
}



/* 08012ce8 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

int FUN_08012ce8(void)

{
  int iVar1;
  
  if (_DAT_2001c278 == 0) {
    iVar1 = 1;
  }
  else {
    iVar1 = (uint)(_DAT_2001c27c == 0) << 1;
  }
  return iVar1;
}



/* 08012d08 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined4 FUN_08012d08(void)

{
  return _DAT_2001c280;
}



/* 08012d28 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined4 FUN_08012d28(void)

{
  uint *puVar1;
  bool bVar2;
  int *piVar3;
  int *piVar4;
  int iVar5;
  uint uVar6;
  undefined4 uVar7;
  uint uVar8;
  
  piVar4 = _DAT_2001c288;
  piVar3 = _DAT_2001c284;
  if (_DAT_2001c27c != 0) {
    _DAT_2001c29c = _DAT_2001c29c + 1;
    FUN_080112a4();
    return 0;
  }
  uVar8 = _DAT_2001c280 + 1;
  if (_DAT_2001c280 == -1) {
    if (*_DAT_2001c284 != 0) {
      bVar2 = (bool)isCurrentModePrivileged();
      if (bVar2) {
        setBasePriority(0x50);
      }
      InstructionSynchronizationBarrier(0xf);
      DataSynchronizationBarrier(0xf);
      do {
                    /* WARNING: Do nothing block with infinite loop */
      } while( true );
    }
    _DAT_2001c284 = _DAT_2001c288;
    _DAT_2001c288 = piVar3;
    _DAT_2001c2a0 = _DAT_2001c2a0 + 1;
    if (*piVar4 == 0) {
      _DAT_2001c294 = 0xffffffff;
    }
    else {
      _DAT_2001c294 = *(uint *)(*(int *)(piVar4[3] + 0xc) + 4);
    }
  }
  _DAT_2001c280 = uVar8;
  if (uVar8 < _DAT_2001c294) {
    uVar7 = 0;
    uVar6 = _DAT_2001c294;
  }
  else {
    uVar7 = 0;
    iVar5 = *_DAT_2001c284;
    while (iVar5 != 0) {
      iVar5 = *(int *)(_DAT_2001c284[3] + 0xc);
      puVar1 = (uint *)(iVar5 + 4);
      uVar6 = *puVar1;
      if (uVar8 < *puVar1) goto LAB_08012e0e;
      FUN_08011244(puVar1);
      if (*(int *)(iVar5 + 0x28) != 0) {
        FUN_08011244(iVar5 + 0x18);
      }
      uVar6 = *(uint *)(iVar5 + 0x2c);
      if (_DAT_2001c28c < uVar6) {
        _DAT_2001c28c = uVar6;
      }
      FUN_08011330(&DAT_2001e910 + uVar6 * 0x14,puVar1);
      if (*(uint *)(_DAT_2001c268 + 0x2c) <= *(uint *)(iVar5 + 0x2c)) {
        uVar7 = 1;
      }
      iVar5 = *_DAT_2001c284;
    }
    uVar6 = 0xffffffff;
  }
LAB_08012e0e:
  _DAT_2001c294 = uVar6;
  if (1 < *(uint *)(&DAT_2001e910 + *(int *)(_DAT_2001c268 + 0x2c) * 0x14)) {
    uVar7 = 1;
  }
  if (_DAT_2001c29c == 0) {
    FUN_080112a4();
  }
  if (_DAT_2001c298 != 0) {
    uVar7 = 1;
  }
  return uVar7;
}



/* 08012e3c */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined4 FUN_08012e3c(int param_1)

{
  bool bVar1;
  uint uVar2;
  int iVar3;
  undefined4 uVar4;
  
  if (param_1 == 0) {
    return 0;
  }
  if (param_1 != _DAT_2001c268) {
    bVar1 = (bool)isCurrentModePrivileged();
    if (bVar1) {
      setBasePriority(0x50);
    }
    InstructionSynchronizationBarrier(0xf);
    DataSynchronizationBarrier(0xf);
    do {
                    /* WARNING: Do nothing block with infinite loop */
    } while( true );
  }
  if (*(int *)(param_1 + 0x50) != 0) {
    iVar3 = *(int *)(param_1 + 0x50) + -1;
    *(int *)(param_1 + 0x50) = iVar3;
    uVar4 = 0;
    if (iVar3 == 0) {
      if (*(int *)(param_1 + 0x2c) != *(int *)(param_1 + 0x4c)) {
        FUN_08011244(param_1 + 4);
        uVar2 = *(uint *)(param_1 + 0x4c);
        *(uint *)(param_1 + 0x2c) = uVar2;
        *(uint *)(param_1 + 0x18) = 0x38 - uVar2;
        if (_DAT_2001c28c < uVar2) {
          _DAT_2001c28c = uVar2;
        }
        FUN_08011330(&DAT_2001e910 + uVar2 * 0x14,param_1 + 4);
        uVar4 = 1;
      }
    }
    return uVar4;
  }
  bVar1 = (bool)isCurrentModePrivileged();
  if (bVar1) {
    setBasePriority(0x50);
  }
  InstructionSynchronizationBarrier(0xf);
  DataSynchronizationBarrier(0xf);
  do {
                    /* WARNING: Do nothing block with infinite loop */
  } while( true );
}



/* 08012ecc */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

bool FUN_08012ecc(int param_1)

{
  uint uVar1;
  
  if (param_1 == 0) {
    return false;
  }
  if (*(uint *)(param_1 + 0x2c) < *(uint *)(_DAT_2001c268 + 0x2c)) {
    if (-1 < *(int *)(param_1 + 0x18)) {
      *(int *)(param_1 + 0x18) = 0x38 - *(int *)(_DAT_2001c268 + 0x2c);
    }
    if (*(undefined1 **)(param_1 + 0x14) == &DAT_2001e910 + *(uint *)(param_1 + 0x2c) * 0x14) {
      FUN_08011244(param_1 + 4);
      uVar1 = *(uint *)(_DAT_2001c268 + 0x2c);
      *(uint *)(param_1 + 0x2c) = uVar1;
      if (_DAT_2001c28c < uVar1) {
        _DAT_2001c28c = uVar1;
      }
      FUN_08011330(&DAT_2001e910 + uVar1 * 0x14,param_1 + 4);
      return true;
    }
    *(undefined4 *)(param_1 + 0x2c) = *(undefined4 *)(_DAT_2001c268 + 0x2c);
    return true;
  }
  return *(uint *)(param_1 + 0x4c) < *(uint *)(_DAT_2001c268 + 0x2c);
}



/* 08012ed4 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

bool FUN_08012ed4(int param_1)

{
  uint uVar1;
  
  if (*(uint *)(_DAT_2001c268 + 0x2c) <= *(uint *)(param_1 + 0x2c)) {
    return *(uint *)(param_1 + 0x4c) < *(uint *)(_DAT_2001c268 + 0x2c);
  }
  if (-1 < *(int *)(param_1 + 0x18)) {
    *(int *)(param_1 + 0x18) = 0x38 - *(int *)(_DAT_2001c268 + 0x2c);
  }
  if (*(undefined1 **)(param_1 + 0x14) != &DAT_2001e910 + *(uint *)(param_1 + 0x2c) * 0x14) {
    *(undefined4 *)(param_1 + 0x2c) = *(undefined4 *)(_DAT_2001c268 + 0x2c);
    return true;
  }
  FUN_08011244(param_1 + 4);
  uVar1 = *(uint *)(_DAT_2001c268 + 0x2c);
  *(uint *)(param_1 + 0x2c) = uVar1;
  if (_DAT_2001c28c < uVar1) {
    _DAT_2001c28c = uVar1;
  }
  FUN_08011330(&DAT_2001e910 + uVar1 * 0x14,param_1 + 4);
  return true;
}



/* 08012f5c */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_08012f5c(int param_1)

{
  bool bVar1;
  undefined1 *puVar2;
  uint uVar3;
  int iVar4;
  int iVar5;
  
  iVar5 = *(int *)(*(int *)(param_1 + 0xc) + 0xc);
  if (iVar5 != 0) {
    iVar4 = iVar5 + 0x18;
    FUN_08011244(iVar4);
    if (_DAT_2001c27c == 0) {
      iVar4 = iVar5 + 4;
      FUN_08011244(iVar4);
      uVar3 = *(uint *)(iVar5 + 0x2c);
      if (_DAT_2001c28c < uVar3) {
        _DAT_2001c28c = uVar3;
      }
      puVar2 = &DAT_2001e910 + uVar3 * 0x14;
    }
    else {
      puVar2 = &DAT_2001c2cc;
    }
    FUN_08011330(puVar2,iVar4);
    if (*(uint *)(_DAT_2001c268 + 0x2c) < *(uint *)(iVar5 + 0x2c)) {
      _DAT_2001c298 = 1;
    }
    return;
  }
  bVar1 = (bool)isCurrentModePrivileged();
  if (bVar1) {
    setBasePriority(0x50);
  }
  InstructionSynchronizationBarrier(0xf);
  DataSynchronizationBarrier(0xf);
  do {
                    /* WARNING: Do nothing block with infinite loop */
  } while( true );
}



/* 08012fd0 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined4 FUN_08012fd0(void)

{
  bool bVar1;
  uint uVar2;
  int iVar3;
  int iVar4;
  
  if (_DAT_2001c27c == 0) {
    bVar1 = (bool)isCurrentModePrivileged();
    if (bVar1) {
      setBasePriority(0x50);
    }
    InstructionSynchronizationBarrier(0xf);
    DataSynchronizationBarrier(0xf);
    do {
                    /* WARNING: Do nothing block with infinite loop */
    } while( true );
  }
  FUN_08011360();
  _DAT_2001c27c = _DAT_2001c27c + -1;
  if ((_DAT_2001c27c == 0) && (_DAT_2001c274 != 0)) {
    if (_DAT_2001c2cc != 0) {
      do {
        iVar4 = *(int *)(_DAT_2001c2d8 + 0xc);
        FUN_08011244(iVar4 + 0x18);
        FUN_08011244(iVar4 + 4);
        uVar2 = *(uint *)(iVar4 + 0x2c);
        if (_DAT_2001c28c < uVar2) {
          _DAT_2001c28c = uVar2;
        }
        FUN_08011330(&DAT_2001e910 + uVar2 * 0x14,iVar4 + 4);
        if (*(uint *)(_DAT_2001c268 + 0x2c) <= *(uint *)(iVar4 + 0x2c)) {
          _DAT_2001c298 = 1;
        }
      } while (_DAT_2001c2cc != 0);
      if (*_DAT_2001c284 == 0) {
        _DAT_2001c294 = 0xffffffff;
      }
      else {
        _DAT_2001c294 = *(undefined4 *)(*(int *)(_DAT_2001c284[3] + 0xc) + 4);
      }
    }
    iVar4 = _DAT_2001c29c;
    if (_DAT_2001c29c != 0) {
      do {
        iVar3 = FUN_08012d28();
        if (iVar3 != 0) {
          _DAT_2001c298 = 1;
        }
        iVar4 = iVar4 + -1;
      } while (iVar4 != 0);
      _DAT_2001c29c = 0;
    }
    if (_DAT_2001c298 != 0) {
      _DAT_e000ed04 = 0x10000000;
      DataSynchronizationBarrier(0xf);
      InstructionSynchronizationBarrier(0xf);
      FUN_080113a8();
      return 1;
    }
  }
  FUN_080113a8();
  return 0;
}



/* 080130c0 */

int FUN_080130c0(undefined4 param_1,undefined4 param_2,undefined4 param_3,undefined4 param_4,
                undefined4 param_5)

{
  int iVar1;
  
  iVar1 = FUN_0800ee94(0x2c);
  if (iVar1 != 0) {
    *(undefined1 *)(iVar1 + 0x28) = 0;
    FUN_0800e814(param_1,param_2,param_3,param_4,param_5,iVar1);
  }
  return iVar1;
}



/* 080130fc */

/* WARNING: Removing unreachable block (ram,0x08013128) */
/* WARNING: Removing unreachable block (ram,0x0801312c) */
/* WARNING: Removing unreachable block (ram,0x08013130) */
/* WARNING: Removing unreachable block (ram,0x08013138) */

int FUN_080130fc(void)

{
  bool bVar1;
  int in_stack_00000004;
  
  if (in_stack_00000004 == 0) {
    bVar1 = (bool)isCurrentModePrivileged();
    if (bVar1) {
      setBasePriority(0x50);
    }
    InstructionSynchronizationBarrier(0xf);
    DataSynchronizationBarrier(0xf);
    do {
                    /* WARNING: Do nothing block with infinite loop */
    } while( true );
  }
  *(undefined1 *)(in_stack_00000004 + 0x28) = 2;
  FUN_0800e814();
  return in_stack_00000004;
}



/* 08013150 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined4 FUN_08013150(void)

{
  bool bVar1;
  undefined4 local_1c;
  undefined4 local_18;
  undefined4 local_14;
  
  FUN_08011360();
  if (_DAT_2001c2e0 == 0) {
    FUN_080112ac(0x2001c2f4);
    FUN_080112ac(0x2001c308);
    _DAT_2001c2e8 = 0x2001c2f4;
    _DAT_2001c2ec = 0x2001c308;
    _DAT_2001c2e0 = FUN_08011f9c(10,0x10,0x2001e810,0x2001e8b0,0);
    if (_DAT_2001c2e0 != 0) {
      FUN_0801154c(_DAT_2001c2e0,&LAB_08013846_1);
    }
  }
  FUN_080113a8();
  if (_DAT_2001c2e0 != 0) {
    local_18 = 0;
    local_14 = 0;
    FUN_08011284(&local_14,&local_18,&local_1c);
    _DAT_2001c2e4 = FUN_08012c64(&LAB_0800e92c_1,s_Tmr_Svc_080131fc,local_1c,0,2,local_18,local_14);
    if (_DAT_2001c2e4 != 0) {
      return 1;
    }
  }
  bVar1 = (bool)isCurrentModePrivileged();
  if (bVar1) {
    setBasePriority(0x50);
  }
  InstructionSynchronizationBarrier(0xf);
  DataSynchronizationBarrier(0xf);
  do {
                    /* WARNING: Do nothing block with infinite loop */
  } while( true );
}



/* 08013204 */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined4
FUN_08013204(int param_1,int param_2,undefined4 param_3,undefined4 param_4,undefined4 param_5)

{
  bool bVar1;
  int iVar2;
  undefined4 uVar3;
  int local_18;
  undefined4 uStack_14;
  int local_10;
  
  if (param_1 == 0) {
    bVar1 = (bool)isCurrentModePrivileged();
    if (bVar1) {
      setBasePriority(0x50);
    }
    InstructionSynchronizationBarrier(0xf);
    DataSynchronizationBarrier(0xf);
    do {
                    /* WARNING: Do nothing block with infinite loop */
    } while( true );
  }
  if (_DAT_2001c2e0 == 0) {
    return 0;
  }
  local_18 = param_2;
  uStack_14 = param_3;
  local_10 = param_1;
  if (5 < param_2) {
    uVar3 = FUN_08012338(_DAT_2001c2e0,&local_18,param_4,0);
    return uVar3;
  }
  iVar2 = FUN_08012ce8();
  if (iVar2 == 2) {
    uVar3 = FUN_08012078(_DAT_2001c2e0,&local_18,param_5,0);
    return uVar3;
  }
  uVar3 = FUN_08012078(_DAT_2001c2e0,&local_18,0,0);
  return uVar3;
}



/* 0801327a */

undefined4 FUN_0801327a(int param_1)

{
  if (param_1 - 0x30U < 10) {
    return 1;
  }
  return 0;
}



/* 08013288 */

/* WARNING: Removing unreachable block (ram,0x08000c38) */
/* WARNING: Removing unreachable block (ram,0x08000c12) */
/* WARNING: Removing unreachable block (ram,0x08000cc0) */
/* WARNING: Removing unreachable block (ram,0x08000cce) */

uint FUN_08013288(byte param_1,undefined4 *param_2)

{
  uint uVar1;
  undefined4 uVar2;
  byte *pbVar3;
  int iVar4;
  uint uVar5;
  byte *pbVar6;
  uint uVar7;
  uint uVar8;
  
  if (0 < (int)param_2[2]) {
    param_2[2] = param_2[2] + -1;
    pbVar3 = (byte *)param_2[1];
    param_2[1] = pbVar3 + 1;
    *pbVar3 = param_1;
    return (uint)param_1;
  }
  uVar1 = param_2[3];
  param_2[3] = uVar1 & 0xffd7ffff | 0x400000;
  if ((int)(uVar1 << 0x1a) < 0) {
    FUN_08000f76(param_2);
  }
  uVar1 = param_2[3];
  if ((uVar1 & 0x1082) != 2) {
    FUN_08000eb0(param_2);
    return 0xffffffff;
  }
  if ((uVar1 & 0xa000) == 0x8000) {
    if ((int)(uVar1 << 0xf) < 0) {
      uVar1 = param_2[0xb];
      if ((uint)param_2[0xb] <= (uint)param_2[1]) {
        uVar1 = param_2[1];
      }
      param_2[1] = uVar1;
    }
    else {
      param_2[0xb] = param_2[4];
      param_2[1] = param_2[4];
      uVar2 = FUN_0800b634(param_2[5]);
      param_2[6] = uVar2;
    }
  }
  uVar1 = (uint)param_1;
  if (((int)param_2[2] < 0) && (-1 < (int)(param_2[3] << 0x16))) {
    param_2[2] = ~param_2[2];
    *param_2 = 0;
    param_2[3] = param_2[3] | 0x12000;
    pbVar3 = (byte *)param_2[1];
    param_2[1] = pbVar3 + 1;
    *pbVar3 = param_1;
    return uVar1;
  }
  *param_2 = 0;
  param_2[3] = param_2[3] | 0x2000;
  if (param_2[4] != 0) goto LAB_08000bec;
  iVar4 = FUN_0800b638(param_2[5]);
  if (iVar4 == 0) {
    iVar4 = FUN_080008f2(param_2[7]);
    param_2[4] = iVar4;
    if (iVar4 == 0) goto LAB_08000bb6;
    uVar5 = param_2[3];
    param_2[3] = uVar5 | 0x800;
    if ((uVar5 & 0x300) == 0) {
      uVar5 = uVar5 | 0x900;
      goto LAB_08000be6;
    }
  }
  else {
    if ((*(ushort *)(param_2 + 3) & 0x300) == 0) {
LAB_08000bb6:
      param_2[7] = 1;
      param_2[4] = param_2 + 9;
      uVar5 = param_2[3] & 0xfffffcff | 0x400;
    }
    else {
      iVar4 = FUN_080008f2(param_2[7]);
      param_2[4] = iVar4;
      if (iVar4 == 0) goto LAB_08000bb6;
      uVar5 = param_2[3] | 0x800;
    }
LAB_08000be6:
    param_2[3] = uVar5;
  }
  param_2[1] = param_2[4];
LAB_08000bec:
  pbVar3 = (byte *)param_2[4];
  if ((int)(param_2[3] << 0x17) < 0) {
    uVar5 = param_2[0xb];
    if ((uint)param_2[0xb] <= (uint)param_2[1]) {
      uVar5 = param_2[1];
    }
    if ((uVar5 - (int)pbVar3 == 0) ||
       (iVar4 = FUN_08000ec4(pbVar3,uVar5 - (int)pbVar3,param_2), uVar5 = 0xffffffff, iVar4 == 0)) {
      param_2[0xb] = pbVar3 + 1;
      param_2[1] = pbVar3 + 1;
      param_2[2] = param_2[7] + -1;
      param_2[3] = param_2[3] | 0x10000;
      *pbVar3 = param_1;
      uVar5 = uVar1;
    }
  }
  else {
    pbVar6 = (byte *)param_2[1];
    param_2[1] = pbVar6 + 1;
    *pbVar6 = param_1;
    param_2[3] = param_2[3] | 0x10000;
    uVar8 = param_2[0xb];
    uVar7 = param_2[1];
    uVar5 = uVar7;
    if (uVar7 < uVar8) {
      uVar5 = uVar8;
    }
    iVar4 = uVar5 - (int)pbVar3;
    if ((((int)((uint)*(ushort *)(param_2 + 3) << 0x15) < 0) || ((int)param_2[7] <= iVar4)) ||
       (uVar5 = uVar1, uVar1 == 10)) {
      if (uVar8 <= uVar7) {
        uVar8 = uVar7;
      }
      param_2[0xb] = pbVar3;
      param_2[1] = pbVar3;
      param_2[2] = 0;
      if (((iVar4 < 1) ||
          (iVar4 = FUN_08000ec4(pbVar3,iVar4,param_2), uVar5 = 0xffffffff, iVar4 == 0)) &&
         (uVar5 = uVar1, uVar8 - uVar7 != 0)) {
        param_2[0xb] = pbVar3;
        param_2[1] = pbVar3;
        param_2[6] = param_2[6] - (uVar8 - uVar7);
        param_2[3] = param_2[3] | 0x10;
      }
    }
  }
  return uVar5;
}



/* 080132a4 */

uint FUN_080132a4(void)

{
  uint in_fpscr;
  
  return in_fpscr & 0xfc3f0000 | 0x3000000;
}



