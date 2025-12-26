
import React from "react";
export default function CardContainer({title, children}){
  return (
    <div className="card">
      {title && <h3 style={{marginTop:0}}>{title}</h3>}
      {children}
    </div>
  );
}
