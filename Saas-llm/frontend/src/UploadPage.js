import React, { useState } from "react";
import axios from "axios";

function UploadPage() {
  const [file, setFile] = useState(null);
  const [files, setFiles] = useState([]);
  const [message, setMessage] = useState("");

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleUpload = async () => {
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);
    try {
      await axios.post("/files/upload", formData, {
        headers: { Authorization: `Bearer <JWT>` },
      });
      setMessage("Upload successful!");
      setFiles([...files, file.name]);
    } catch (err) {
      setMessage("Upload failed.");
    }
  };

  return (
    <div className="p-8 max-w-xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">Upload PDF</h1>
      <input type="file" accept="application/pdf" onChange={handleFileChange} />
      <button className="bg-blue-500 text-white px-4 py-2 mt-2" onClick={handleUpload}>Upload</button>
      <div className="mt-4 text-green-600">{message}</div>
      <h2 className="mt-8 text-xl font-semibold">Uploaded Files</h2>
      <ul className="list-disc ml-6">
        {files.map((f) => (
          <li key={f}>{f}</li>
        ))}
      </ul>
    </div>
  );
}

export default UploadPage;
