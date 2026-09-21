import styles from './Placeholder.module.css'
export function Placeholder({title,description}:{title:string;description:string}) { return <section className={styles.card}><p className={styles.eyebrow}>Coming in a later phase</p><h1 className={styles.title}>{title}</h1><p className={styles.copy}>{description}</p></section> }
