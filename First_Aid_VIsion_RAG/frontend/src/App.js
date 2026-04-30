import React, { useCallback, useRef, useState } from 'react';
import Webcam from 'react-webcam';
import axios from 'axios';
import './App.css';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://127.0.0.1:8001';

function App() {
    const webcamRef = useRef(null);
    const [imgSrc, setImgSrc] = useState(null);
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);

    const resetToCamera = useCallback(() => {
        setImgSrc(null);
        setResult(null);
    }, []);

    const captureAndAnalyze = useCallback(async () => {
        if (result) {
            resetToCamera();
            return;
        }

        const imageSrc = webcamRef.current?.getScreenshot();
        if (!imageSrc) {
            return;
        }

        setImgSrc(imageSrc);
        setLoading(true);
        setResult(null);

        try {
            const blob = await fetch(imageSrc).then((res) => res.blob());
            const formData = new FormData();
            formData.append('file', blob, 'capture.jpg');

            const response = await axios.post(`${API_BASE_URL}/analyze`, formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
                timeout: 60000,
            });
            setResult(response.data);
        } catch (error) {
            console.error('Error analyzing image:', error);

            let serverMessage = '서버를 확인한 뒤 다시 시도해주세요.';
            if (error.code === 'ERR_NETWORK') {
                serverMessage = `백엔드 서버(${API_BASE_URL})에 연결할 수 없습니다. run_backend.bat를 실행했는지 확인해주세요.`;
            } else if (error.response?.data?.suggestion) {
                serverMessage = error.response.data.suggestion;
            } else if (error.response?.data?.detail) {
                serverMessage = error.response.data.detail;
            } else if (error.message) {
                serverMessage = error.message;
            }

            setResult({
                analysis: '분석 실패',
                suggestion: serverMessage,
            });
        } finally {
            setLoading(false);
        }
    }, [resetToCamera, result]);

    return (
        <div className="App">
            <header className="App-header">
                <h1>First-Aid Vision AI</h1>
                <div className="main-layout">
                    <div className="camera-section">
                        {loading || result ? (
                            <div className="captured-preview">
                                <img src={imgSrc} alt="captured" className="webcam-view" />
                                {loading && <div className="loading-overlay">AI 분석 중...</div>}
                            </div>
                        ) : (
                            <Webcam
                                audio={false}
                                ref={webcamRef}
                                screenshotFormat="image/jpeg"
                                screenshotQuality={0.7}
                                className="webcam-view"
                                mirrored={true}
                                videoConstraints={{
                                    width: 640,
                                    height: 480,
                                    facingMode: 'environment',
                                }}
                            />
                        )}

                        <button className="capture-btn" onClick={captureAndAnalyze} disabled={loading}>
                            {loading ? 'AI 분석 중...' : result ? '다시 촬영하기' : '응급 상황 분석 요청'}
                        </button>
                    </div>

                    <div className="result-section">
                        <h3>분석 및 조치 가이드</h3>
                        {result ? (
                            <div className="result-content">
                                <div className="result-item">
                                    <strong>상황 판단:</strong> {result.analysis}
                                </div>
                                <div className="result-item">
                                    <strong>조치 가이드:</strong> {result.suggestion}
                                </div>
                            </div>
                        ) : (
                            <p className="placeholder">
                                카메라를 비춘 뒤 버튼을 누르면 AI 가이드가 제공됩니다.
                            </p>
                        )}
                    </div>
                </div>
            </header>
        </div>
    );
}

export default App;
