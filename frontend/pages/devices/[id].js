export async function getServerSideProps(context) {
  return { props: { id: context.params.id } };
}

export default function DeviceDetailPage({ id }) {
  return (
    <main>
      <h1>Device {id}</h1>
    </main>
  );
}
