import React, {useState, useRef, useCallback} from 'react';
import Webcam from 'react-webcam';
import axios from 'axios';
import './App.css';

function App(){
    const webcamRef = useRef(null);
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);

    // 사진을 캡쳐해서 백엔드로 전송하는 함수
    const captureAndAnalyze = useCallback(async () => {
        const imageSrc = webcamRef.current.getScreenshot();
        if(!imageSrc) return;

        try{
            // 이미지를 서버가 받을 수 있는 blob으로 변환
            const blob = await fetch(imsageSrc).then((res) => res.blob());
            const formData = new FormData();
            formData.append('file', blob, 'capture.jpg');

            // 백엔드 호출
            const response = await axios.post('httpL//127.0.0.1:8000/analyze', formData, {
                headers: {'Content-Type': 'multipart/form-data'},
            });
            setResult(response.data);
         }catch(error){
            console.error('Error analyzing image:', error);
            setResult({analysis:'Error occured', suggestions: 'check the server and try again'});
            }finally{
                setLoading(false);
            }
    }, [webcamRef]);
    
    return(
        <div className="App">
            <header className="App-header">
                <h1>First-Aid Vision AI</h1>
                <div className="main-layout">
                {/* 웹캠 섹션 */}
                <div className="camera-section">
                    <Webcam
                    audio={false}
                    ref={webcamRef}
                    screenshotFormat="image/jpeg"
                    className="webcam-view"
                    />
                    <button className="capture-btn" onClick={captureAndAnalyze} disabled={loading}>
                    {loading ? "AI 분석 중..." : "응급 상황 분석 요청"}
                    </button>
                </div>

                {/* 결과 섹션 */}
                <div className="result-section">
                    <h3>🚑 분석 및 조치 가이드</h3>
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
                    <p className="placeholder">카메라를 비추고 버튼을 누르면 AI 가이드가 제공됩니다.</p>
                    )}
                </div>
                </div>
            </header>
        </div>
    );
}

export default App;