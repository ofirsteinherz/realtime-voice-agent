// Three.js Character Component - Pharmacist
let scene, camera, renderer, character, head, leftEye, rightEye, mouth;
let isListening = false;
let analyser, dataArray;
let sensitivity = 1;

const VISEMES = {
    SILENT: { scaleY: 0.4, scaleX: 1.0, posY: -0.18 },
    AA: { scaleY: 1.2, scaleX: 0.9, posY: -0.22 },
    E: { scaleY: 0.6, scaleX: 1.2, posY: -0.19 },
    I: { scaleY: 0.5, scaleX: 1.3, posY: -0.18 },
    O: { scaleY: 0.9, scaleX: 0.8, posY: -0.20 },
    U: { scaleY: 0.7, scaleX: 0.7, posY: -0.19 },
    PP: { scaleY: 0.3, scaleX: 0.9, posY: -0.18 },
    SS: { scaleY: 0.45, scaleX: 1.05, posY: -0.18 },
};

let targetViseme = VISEMES.SILENT;

function initCharacter() {
    const canvas = document.getElementById('canvas');
    scene = new THREE.Scene();
    scene.background = null;
    
    camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.set(0, 0.9, 5);
    camera.lookAt(0, 0.9, 0);
    
    renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.shadowMap.enabled = true;
    renderer.setClearColor(0x000000, 0);
    
    // Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
    scene.add(ambientLight);
    
    const keyLight = new THREE.DirectionalLight(0xffffff, 0.6);
    keyLight.position.set(5, 8, 5);
    keyLight.castShadow = true;
    scene.add(keyLight);
    
    const fillLight = new THREE.DirectionalLight(0xffffff, 0.25);
    fillLight.position.set(-5, 3, 3);
    scene.add(fillLight);
    
    // Ground shadow
    const groundGeometry = new THREE.PlaneGeometry(10, 10);
    const groundMaterial = new THREE.ShadowMaterial({ opacity: 0.2 });
    const ground = new THREE.Mesh(groundGeometry, groundMaterial);
    ground.rotation.x = -Math.PI / 2;
    ground.position.y = -0.6;
    ground.receiveShadow = true;
    scene.add(ground);
    
    createPharmacist();
    animate();
}

function createPharmacist() {
    character = new THREE.Group();
    character.position.x = -1.1;
    scene.add(character);
    
    const skinColor = 0xf5d0a9;
    
    // Head
    const headGeometry = new THREE.SphereGeometry(0.6, 32, 32);
    const headMaterial = new THREE.MeshStandardMaterial({ color: skinColor, roughness: 0.9 });
    head = new THREE.Mesh(headGeometry, headMaterial);
    head.position.y = 1.5;
    head.castShadow = true;
    character.add(head);
    
    // Eyes
    const eyeGeometry = new THREE.SphereGeometry(0.08, 16, 16);
    const eyeMaterial = new THREE.MeshStandardMaterial({ color: 0x2c3e50 });
    
    leftEye = new THREE.Mesh(eyeGeometry, eyeMaterial);
    leftEye.position.set(-0.18, 0.15, 0.5);
    head.add(leftEye);
    
    rightEye = new THREE.Mesh(eyeGeometry, eyeMaterial);
    rightEye.position.set(0.18, 0.15, 0.5);
    head.add(rightEye);
    
    // Eye highlights
    const highlightGeometry = new THREE.SphereGeometry(0.025, 8, 8);
    const highlightMaterial = new THREE.MeshBasicMaterial({ color: 0xffffff });
    
    const leftHighlight = new THREE.Mesh(highlightGeometry, highlightMaterial);
    leftHighlight.position.set(-0.03, 0.03, 0.065);
    leftEye.add(leftHighlight);
    
    const rightHighlight = new THREE.Mesh(highlightGeometry, highlightMaterial);
    rightHighlight.position.set(-0.03, 0.03, 0.065);
    rightEye.add(rightHighlight);
    
    // Glasses
    const glassesGroup = new THREE.Group();
    const lensGeometry = new THREE.TorusGeometry(0.12, 0.015, 8, 20);
    const glassesMaterial = new THREE.MeshStandardMaterial({ 
        color: 0x34495e,
        metalness: 0.6,
        roughness: 0.2
    });
    
    const leftLens = new THREE.Mesh(lensGeometry, glassesMaterial);
    leftLens.position.set(-0.18, 0.15, 0.5);
    glassesGroup.add(leftLens);
    
    const rightLens = new THREE.Mesh(lensGeometry, glassesMaterial);
    rightLens.position.set(0.18, 0.15, 0.5);
    glassesGroup.add(rightLens);
    
    const bridgeGeometry = new THREE.CylinderGeometry(0.015, 0.015, 0.12, 8);
    const bridge = new THREE.Mesh(bridgeGeometry, glassesMaterial);
    bridge.rotation.z = Math.PI / 2;
    bridge.position.set(0, 0.15, 0.5);
    glassesGroup.add(bridge);
    
    head.add(glassesGroup);
    
    // Eyebrows
    const eyebrowGeometry = new THREE.BoxGeometry(0.22, 0.035, 0.05);
    const eyebrowMaterial = new THREE.MeshStandardMaterial({ color: 0x6d4c41 });
    
    const leftEyebrow = new THREE.Mesh(eyebrowGeometry, eyebrowMaterial);
    leftEyebrow.position.set(-0.18, 0.32, 0.48);
    leftEyebrow.rotation.z = 0.08;
    head.add(leftEyebrow);
    
    const rightEyebrow = new THREE.Mesh(eyebrowGeometry, eyebrowMaterial);
    rightEyebrow.position.set(0.18, 0.32, 0.48);
    rightEyebrow.rotation.z = -0.08;
    head.add(rightEyebrow);
    
    // Nose
    const noseGeometry = new THREE.ConeGeometry(0.08, 0.15, 8);
    const noseMaterial = new THREE.MeshStandardMaterial({ color: 0xffcca3, roughness: 0.8 });
    const nose = new THREE.Mesh(noseGeometry, noseMaterial);
    nose.position.set(0, 0.05, 0.58);
    nose.rotation.x = Math.PI / 2;
    head.add(nose);
    
    // Mouth
    const mouthGeometry = new THREE.SphereGeometry(0.18, 16, 16, 0, Math.PI * 2, 0, Math.PI / 2);
    const mouthMaterial = new THREE.MeshStandardMaterial({ color: 0xff4d6d, roughness: 0.6 });
    mouth = new THREE.Mesh(mouthGeometry, mouthMaterial);
    mouth.position.set(0, -0.18, 0.52);
    mouth.rotation.x = Math.PI;
    mouth.scale.set(1.0, 0.4, 1.0);
    head.add(mouth);
    
    // Hair
    const hairGeometry = new THREE.SphereGeometry(0.62, 32, 32, 0, Math.PI * 2, 0, Math.PI / 2);
    const hairMaterial = new THREE.MeshStandardMaterial({ color: 0x6d4c41, roughness: 0.9 });
    const hair = new THREE.Mesh(hairGeometry, hairMaterial);
    hair.position.y = 0.35;
    head.add(hair);
    
    // Body
    const bodyGeometry = new THREE.CylinderGeometry(0.5, 0.6, 1.2, 20);
    const bodyMaterial = new THREE.MeshStandardMaterial({ color: 0x10b981, roughness: 0.7 });
    const body = new THREE.Mesh(bodyGeometry, bodyMaterial);
    body.position.y = 0.3;
    body.castShadow = true;
    character.add(body);
    
    // Lab coat
    const coatGeometry = new THREE.BoxGeometry(1.1, 1.3, 0.3);
    const coatMaterial = new THREE.MeshStandardMaterial({ color: 0xf5f5f0, roughness: 0.85 });
    const coat = new THREE.Mesh(coatGeometry, coatMaterial);
    coat.position.set(0, 0.3, 0.2);
    coat.castShadow = true;
    character.add(coat);
    
    // Stethoscope
    const stethGeometry = new THREE.TorusGeometry(0.25, 0.02, 8, 30, Math.PI);
    const stethMaterial = new THREE.MeshStandardMaterial({ color: 0x2c3e50, metalness: 0.4 });
    const stethoscope = new THREE.Mesh(stethGeometry, stethMaterial);
    stethoscope.position.set(0, 0.85, 0.3);
    stethoscope.rotation.x = Math.PI / 6;
    character.add(stethoscope);
    
    // Arms
    const armGeometry = new THREE.CylinderGeometry(0.12, 0.1, 0.9, 16);
    const skinMaterial = new THREE.MeshStandardMaterial({ color: skinColor, roughness: 0.9 });
    
    const leftArm = new THREE.Mesh(armGeometry, skinMaterial);
    leftArm.position.set(-0.6, 0.3, 0);
    leftArm.rotation.z = -0.3;
    character.add(leftArm);
    
    const rightArm = new THREE.Mesh(armGeometry, skinMaterial);
    rightArm.position.set(0.6, 0.3, 0);
    rightArm.rotation.z = 0.3;
    character.add(rightArm);
}

function lerp(start, end, t) {
    return start + (end - start) * t;
}

function animate() {
    requestAnimationFrame(animate);
    
    const time = Date.now() * 0.001;
    const baseBreathing = Math.sin(time * 0.8) * 0.03;
    const baseHeadY = Math.sin(time * 0.5) * 0.1;
    const baseHeadX = Math.sin(time * 0.3) * 0.05;
    
    // Blinking
    if (Math.sin(time * 3) > 0.98) {
        leftEye.scale.y = 0.1;
        rightEye.scale.y = 0.1;
    } else {
        leftEye.scale.y = 1;
        rightEye.scale.y = 1;
    }
    
    // Voice animation
    if (isListening && analyser && dataArray) {
        analyser.getByteFrequencyData(dataArray);
        
        const bass = dataArray.slice(0, 60).reduce((a, b) => a + b) / 60;
        const mid = dataArray.slice(60, 120).reduce((a, b) => a + b) / 60;
        const treble = dataArray.slice(120, 180).reduce((a, b) => a + b) / 60;
        
        const sensitivityMultiplier = 0.5 + (sensitivity / 10) * 1.5;
        const adjustedBass = bass * sensitivityMultiplier;
        const adjustedMid = mid * sensitivityMultiplier;
        const adjustedTreble = treble * sensitivityMultiplier;
        
        const threshold = 100 / sensitivityMultiplier;
        if (adjustedBass > threshold) {
            targetViseme = VISEMES.AA;
        } else if (adjustedTreble > threshold) {
            targetViseme = VISEMES.SS;
        } else if (adjustedMid > threshold * 0.8) {
            targetViseme = VISEMES.E;
        } else if (adjustedBass + adjustedMid + adjustedTreble > threshold) {
            targetViseme = VISEMES.O;
        } else {
            targetViseme = VISEMES.SILENT;
        }
        
        const lerpFactor = 0.15;
        mouth.scale.y = lerp(mouth.scale.y, targetViseme.scaleY, lerpFactor);
        mouth.scale.x = lerp(mouth.scale.x, targetViseme.scaleX, lerpFactor);
        mouth.position.y = lerp(mouth.position.y, targetViseme.posY, lerpFactor);
        
        const average = (adjustedBass + adjustedMid + adjustedTreble) / 3;
        const normalizedVolume = Math.min(average / 128, 1);
        
        head.rotation.y = baseHeadY + Math.sin(time * 2) * 0.15 * normalizedVolume;
        head.rotation.x = baseHeadX + Math.sin(time * 1.5) * 0.08 * normalizedVolume;
        character.position.y = baseBreathing + Math.sin(time * 1.5) * 0.05 * normalizedVolume;
    } else {
        targetViseme = VISEMES.SILENT;
        
        const lerpFactor = 0.1;
        mouth.scale.y = lerp(mouth.scale.y, targetViseme.scaleY, lerpFactor);
        mouth.scale.x = lerp(mouth.scale.x, targetViseme.scaleX, lerpFactor);
        mouth.position.y = lerp(mouth.position.y, targetViseme.posY, lerpFactor);
        
        character.position.y = baseBreathing;
        head.rotation.y = baseHeadY;
        head.rotation.x = baseHeadX;
    }
    
    renderer.render(scene, camera);
}

function setCharacterListening(listening, audioAnalyser, audioDataArray) {
    isListening = listening;
    analyser = audioAnalyser;
    dataArray = audioDataArray;
}

// Window resize handler
window.addEventListener('resize', () => {
    if (camera && renderer) {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
    }
});