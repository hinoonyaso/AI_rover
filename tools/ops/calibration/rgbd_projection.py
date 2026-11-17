"""Project raw depth pixels into color space with an explicit rigid transform.

한글: 명시적 강체 변환으로 원본 깊이 픽셀을 컬러 공간에 투영한다.
"""
import cv2
import numpy as np


def project(depth, depth_k, depth_d, color_k, color_d, rotation, translation, output_size):
    """Return color-frame uint16 millimetres with nearest-depth occlusion handling.

    한글: 가려진 점 중 가장 가까운 값으로 컬러 프레임 깊이(mm)를 생성한다.
    """
    if depth.dtype != np.uint16 or depth.ndim != 2:raise ValueError('invalid_depth')
    dk=np.asarray(depth_k,dtype=np.float64).reshape(3,3);ck=np.asarray(color_k,dtype=np.float64).reshape(3,3)
    dd=np.asarray(depth_d,dtype=np.float64);cd=np.asarray(color_d,dtype=np.float64)
    r=np.asarray(rotation,dtype=np.float64);t=np.asarray(translation,dtype=np.float64)
    width,height=output_size
    if (r.shape!=(3,3) or t.shape!=(3,) or not all(np.isfinite(v).all() for v in (dk,ck,dd,cd,r,t))
        or dk[0,0]<=0 or dk[1,1]<=0 or ck[0,0]<=0 or ck[1,1]<=0 or not np.allclose(r.T@r,np.eye(3),atol=1e-4)
        or abs(np.linalg.det(r)-1)>1e-4 or np.max(np.abs(t))>2 or not 0<width<=4096 or not 0<height<=4096):raise ValueError('invalid_calibration')
    y,x=np.nonzero(depth);out=np.zeros((height,width),dtype=np.uint16)
    if not len(x):return out
    pixels=np.stack((x,y),axis=-1).astype(np.float64).reshape(-1,1,2)
    normalized=cv2.undistortPoints(pixels,dk,dd).reshape(-1,2)
    z=depth[y,x].astype(np.float64)*.001
    points=np.column_stack((normalized*z[:,None],z));points=points@r.T+t
    valid=np.isfinite(points).all(axis=1)&(points[:,2]>.001)&(points[:,2]<65.535)
    points=points[valid]
    if not len(points):return out
    projected,_=cv2.projectPoints(points,np.zeros(3),np.zeros(3),ck,cd)
    uv=np.rint(projected.reshape(-1,2)).astype(np.int64);valid=(uv[:,0]>=0)&(uv[:,0]<width)&(uv[:,1]>=0)&(uv[:,1]<height)
    uv=uv[valid];values=np.rint(points[valid,2]*1000).astype(np.uint16)
    # Minimum positive depth is the visible surface when projected pixels collide.
    # 한글: 여러 깊이점이 겹치면 가장 가까운 표면의 깊이를 사용한다.
    flat=np.full(width*height,65535,dtype=np.uint16);np.minimum.at(flat,uv[:,1]*width+uv[:,0],values)
    flat[flat==65535]=0
    return flat.reshape(height,width)
